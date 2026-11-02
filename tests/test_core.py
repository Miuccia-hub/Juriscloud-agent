from dataclasses import asdict
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile
from pathlib import Path
import pytest
from docx import Document
from docx.oxml.ns import qn
from lxml import etree

from legal_agent.documents import extract,validate_bundle
from tests.fixture_data import load_demo
from legal_agent.models import *
from legal_agent.edits import check_conflicts,merge_choices
from legal_agent.exports import revised_docx,report_sections,report_docx,report_pdf,embed_report_font
from legal_agent.research import allowed_url,retrieve,quote_exists
from legal_agent.workflow import Workflow,guard_report,Gateway


def test_invalid_input_and_limits():
    with pytest.raises(ValueError): extract("bad.doc",b"x")
    with pytest.raises(ValueError): extract("a.txt",b"")
    with pytest.raises(ValueError): extract("a.txt",("长"*60001).encode())
    main,*_=load_demo()
    with pytest.raises(ValueError): validate_bundle(main,[main]*7)


def test_source_host_boundary():
    roots=["court.gov.cn","austlii.edu.au"]
    assert allowed_url("https://www.court.gov.cn/x",roots)
    for url in ["http://court.gov.cn", "https://court.gov.cn.evil.com/x", "https://evilcourt.gov.cn", "https://austlii.edu.au@evil.com", "https://court.gov.cn:9000", "https://127.0.0.1"]:
        assert not allowed_url(url,roots)


def test_failed_sources_are_not_evidence():
    def fail(*_): raise TimeoutError()
    sources,notes=retrieve([{"url":"https://www.hcourt.gov.au/judgment","title":"test"}],"维多利亚州",[],fail)
    assert sources[0].status=="正文未取得"
    assert not quote_exists("a fake legal quotation",sources[0])


def test_overlap_and_reconfirmation():
    main,_,_,_,choices=load_demo()
    dup=choices[0].edit.model_copy(update={"id":"OTHER"})
    choices[0].state="采纳"
    merge_choices(choices,[dup],"追问",True)
    choices[1].state="采纳"
    errors=check_conflicts(main,choices)
    assert any("重叠" in e for e in errors)
    assert any("重新确认" in e for e in errors)
    with pytest.raises(ValueError): revised_docx(main,choices)


def test_real_word_revisions_accept_and_reject():
    original=Document()
    original.add_heading("技术合同",0)
    p=original.add_paragraph()
    p.add_run("费用为 ").bold=True
    p.add_run("100 元").italic=True
    p.add_run("，分两次付款。")
    table=original.add_table(rows=1,cols=1)
    table.cell(0,0).text="验收期限五日。"
    buf=BytesIO();original.save(buf)
    main=extract("test.docx",buf.getvalue())
    clause=next(c for c in main.clauses if "100" in c.text)
    edit=ProposedEdit(id="E",risk_id="R",clause_id=clause.id,original="100 元",replacement="200 元",reason="test",source_ids=[],bilingual_note="")
    output=revised_docx(main,[EditChoice(edit,"采纳","200 元")])
    with ZipFile(BytesIO(output)) as z:
        tree=etree.fromstring(z.read("word/document.xml"))
        ns={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        assert tree.xpath("//w:del/w:r/w:delText/text()",namespaces=ns)==["100 元"]
        assert tree.xpath("//w:ins/w:r/w:t/text()",namespaces=ns)==["200 元"]
        assert tree.xpath("//w:ins//w:i",namespaces=ns)
        assert len(tree.xpath("//w:tbl",namespaces=ns))==1
        for accept in (True,False):
            node=etree.fromstring(z.read("word/document.xml"))
            for change in node.xpath("//w:ins | //w:del",namespaces=ns):
                keep=(change.tag==qn("w:ins"))==accept
                if keep:
                    for child in list(change):
                        for t in child.iter(qn("w:delText")): t.tag=qn("w:t")
                        change.addprevious(child)
                change.getparent().remove(change)
            text="".join(node.xpath("//w:t/text()",namespaces=ns))
            assert ("200 元" if accept else "100 元") in text
            assert ("100 元" if accept else "200 元") not in text


def test_table_edit_and_existing_revision_rejection():
    d=Document(); d.add_table(rows=1,cols=1).cell(0,0).text="Tax is included."
    b=BytesIO();d.save(b); main=extract("t.docx",b.getvalue())
    c=main.clauses[0]
    e=ProposedEdit(id="E",risk_id="R",clause_id=c.id,original="included",replacement="excluded",reason="test",source_ids=[],bilingual_note="")
    out=revised_docx(main,[EditChoice(e,"采纳","excluded")])
    assert len(Document(BytesIO(out)).tables)==1
    with pytest.raises(ValueError,match="已有修订"): extract("revised.docx",out)


def test_existing_embedded_font_survives_revision_export():
    d=Document();d.add_paragraph("Price is 100 dollars.")
    b=BytesIO();d.save(b)
    main=extract("font.docx",embed_report_font(b.getvalue()))
    edit=ProposedEdit(id="E",risk_id="R",clause_id=main.clauses[0].id,original="100",replacement="200",reason="test",source_ids=[],bilingual_note="")
    out=revised_docx(main,[EditChoice(edit,"采纳","200")])
    with ZipFile(BytesIO(out)) as z:
        rels=etree.fromstring(z.read("word/_rels/fontTable.xml.rels"))
        ids=[r.get("Id") for r in rels]
        assert len(ids)==len(set(ids))
        for r in rels:
            if r.get("Type","").endswith("/font"):
                assert "word/"+r.get("Target") in z.namelist()


def test_guard_removes_fabricated_anchors_and_downgrades():
    main,_,_,report,_=load_demo()
    r=report.risks[0];r.category="法律效力";r.source_ids=["FAKE"];r.clause_ids.append("WRONG")
    report.suggestions[0].original="invented original"
    guard_report(report,main,[],[],"T")
    assert r.verification=="待核实"
    assert "WRONG" not in r.clause_ids
    assert not report.suggestions


class FakeGateway:
    """Test double only. No model or legal research is performed."""
    def __init__(self): self.calls=[]
    def structured(self,stage,schema,payload,instruction):
        self.calls.append(stage)
        if schema==Intake: return load_demo()[2]
        if schema==Plan: return Plan(scope=["all"],issues=["test"],public_search_queries=["contract acceptance"],missing_information=[])
        if schema==ReviewBatch:
            import re
            match=re.search(r"\[(D1-P\d+)\] ([^\n]+)",payload['documents'])
            return ReviewBatch(checks=[CoverageCheck(check_id=t['id'],status='已分析',assessment='Test-only check record.',
                quotes=[CoverageQuote(clause_id=match[1],quote=match[2])],concern=False,priority='低',next_step='No live legal assessment in this test.') for t in payload['assigned_checks']],
                reviewed_clause_ids=re.findall(r"\[(D1-P\d+)\]",payload['documents']))
        if schema==OmissionAudit:return OmissionAudit(corrected_checks=[],missed_issues=[],limitations=[])
        if schema==ReviewSynthesis:return ReviewSynthesis(**load_demo()[3].model_dump(),check_links=[])
        if schema==Evidence: return Evidence(findings=[],limitations=["test: no real legal sources"])
        if schema==FollowupAnswer: return FollowupAnswer(answered_question=payload["current_question"],direct_answer="Focused test answer to "+payload["current_question"],contract_analysis="Test-only contract analysis.",legal_analysis="No live legal research.",next_steps=[],limitations=[],suggestions=[])
        if schema==Critique: return Critique(defects=[],unsupported_risk_ids=[],conflicting_edit_ids=[],corrections=[])
        return load_demo()[3].model_copy(deep=True)
    def search(self,*args): return []


def test_checklist_review_calls_and_five_followup_calls():
    main,settings,*_=load_demo()
    g=FakeGateway();w=Workflow(g)
    intake=w.intake(main,[],settings)
    report,sources,evidence,critic=w.review(main,[],settings,intake)
    assert len(g.calls)==10 and len(set(g.calls))==10
    assert any("没有取得" in x for x in report.limitations)
    w.followup(main,[],settings,intake,report,[],"why?","")
    assert len(g.calls)==15


def test_gateway_records_failure_without_secret(monkeypatch):
    g=Gateway("test-only-not-a-real-key","test-model")
    def fail(**kwargs): raise TimeoutError("contains no user key")
    monkeypatch.setattr(g.client.responses,"create",fail)
    with pytest.raises(Exception,match="connection"): g.structured("test",Intake,{},"")
    assert len(g.calls)==1 and not g.calls[0].success
    assert "key" not in str(asdict(g.calls[0]))


def test_reports_and_demo_exports():
    main,settings,_,report,choices=load_demo()
    sections=report_sections(report,[],choices,settings)
    doc=report_docx(sections);pdf=report_pdf(sections)
    assert Document(BytesIO(doc)).paragraphs[0].text.startswith("商业")
    from pypdf import PdfReader
    assert len(PdfReader(BytesIO(pdf)).pages)>0
    choices[0].state="采纳"
    with ZipFile(BytesIO(revised_docx(main,choices))) as z:
        assert b"w:delText" in z.read("word/document.xml")



def test_streamlit_home_is_live_and_single_language():
    from tests.ui_helpers import workspace_app
    app=workspace_app(Path(__file__).resolve().parents[1]/"app.py").run(timeout=15)
    assert not app.exception
    assert not any("sample" in b.label.lower() or "示例" in b.label for b in app.button)
    assert not any(" / " in b.label for b in app.button)
    assert app.button(key="send_initial").label=="↑"
    app.selectbox(key="ui_language").set_value("English").run(timeout=15)
    assert not app.exception
    assert any("How can I help?"==x.placeholder for x in app.text_area)
    assert app.selectbox(key="language").value=="自动（跟随问题）"


def test_language_switch_preserves_draft_and_missing_key_blocks():
    from tests.ui_helpers import workspace_app
    app=workspace_app(Path(__file__).resolve().parents[1]/"app.py").run(timeout=15)
    app.radio(key="input_mode").set_value("粘贴文本").run()
    app.text_area(key="contract_text").set_value("Fictional unsent contract draft").run()
    app.text_area(key="initial_question").set_value("Check the payment terms").run()
    app.selectbox(key="ui_language").set_value("English").run()
    assert not app.exception
    assert app.text_area(key="contract_text").value=="Fictional unsent contract draft"
    assert app.text_area(key="initial_question").value=="Check the payment terms"
    app.button(key="send_initial").click().run()
    assert any("API key" in e.value for e in app.error)
    assert "report" not in app.session_state
    app.text_input(key="api_key").set_value("test-not-a-real-key").run()
    next(b for b in app.button if b.label=="Clear session").click().run()
    assert not app.exception
    assert app.selectbox(key="ui_language").value=="English"
    assert app.text_input(key="api_key").value==""


def test_upload_panel_does_not_block_quick_prompt_or_composer():
    from tests.ui_helpers import workspace_app
    app=workspace_app(Path(__file__).resolve().parents[1]/"app.py").run()
    assert app.session_state["upload_open"] is False
    app.button(key="toggle_upload").click().run()
    assert app.session_state["upload_open"] is True
    app.button(key="quick_prompt_1").click().run()
    assert "判例" in app.text_area(key="initial_question").value
    app.button(key="toggle_upload").click().run()
    assert app.session_state["upload_open"] is False
    assert "判例" in app.text_area(key="initial_question").value


def test_upload_decode_and_language_resolution():
    import base64
    from legal_agent.upload import decode_files
    from legal_agent.presentation import answer_language
    raw="Original 合同".encode()
    files=decode_files({"files":[{"name":"contract.txt","data":base64.b64encode(raw).decode()}]},1)
    assert files[0].getvalue()==raw
    with pytest.raises(ValueError): decode_files({"files":[{"name":"x.txt","data":"!"}]},1)
    assert answer_language("自动（跟随问题）","Review this") == "English"
    assert answer_language("自动（跟随问题）","检查合同") == "中文"
    assert answer_language("English","检查合同") == "English"


def test_review_ui_with_test_double(monkeypatch):
    """Exercises UI integration only. FakeGateway does not make live AI requests."""
    from tests.ui_helpers import workspace_app
    import legal_agent.workflow
    class UIGateway(FakeGateway):
        def structured(self,*args):
            result=super().structured(*args)
            if args[1]==Intake:
                result.critical_questions=["An attachment was not provided."]
                result.conflicts=["Governing law differs from the selected scope."]
            self.calls[-1]=Call(self.calls[-1],"test",True,0,0)
            return result
    monkeypatch.setattr(legal_agent.workflow,"Gateway",lambda *args: UIGateway())
    app=workspace_app(Path(__file__).resolve().parents[1]/"app.py").run(timeout=15)
    app.radio(key="input_mode").set_value("粘贴文本").run()
    main,settings,*_=load_demo()
    app.text_area(key="contract_text").set_value("\n".join(c.text for c in main.clauses)).run()
    app.text_area(key="initial_question").set_value("Check payment risk").run()
    app.text_input(key="api_key").set_value("test-only").run()
    app.button(key="send_initial").click().run()
    assert not app.exception
    assert app.session_state["original_question"]=="Check payment risk"
    assert app.session_state["settings"].language=="English"

    assert not app.error
    assert len(app.session_state["gateway"].calls)==10
    assert not any(x.key=="confirm_scope" for x in app.get("form"))
    assert "report" in app.session_state
    assert "Check payment risk" in app.session_state["settings"].focus
    assert "An attachment was not provided." in app.session_state["report"].limitations
    assert "No factual confirmations" in app.session_state["settings"].confirmations
    assert any("review-table" in x.value for x in app.markdown)
    assert any("✓" in x for x in app.session_state["review_trace"])
    # A fresh test renderer avoids Streamlit 1.50's stale removed-form widget tree.
    state={key:app.session_state[key] for key in ("main","supplements","settings","intake","report","choices","sources","evidence","messages","answers","original_question")}
    app=workspace_app(Path(__file__).resolve().parents[1]/"app.py")
    for key,value in state.items(): app.session_state[key]=value
    app.session_state["api_key"]="test-only"
    app.run()
    original=app.session_state["main"].clauses[0].text
    app.selectbox(key="ui_language").set_value("English").run()
    assert not app.exception
    assert app.session_state["main"].clauses[0].text==original
    app.text_area(key="question").set_value("Explain the payment risk").run()
    app.button(key="send_followup").click().run(timeout=15)
    assert not app.exception
    assert len(app.session_state["messages"])==2
    app.radio(key="view").set_value("修改清单 / Edits").run()
    assert not app.exception
    app.radio(key="view").set_value("带走审查结果 / Export your work").run()
    import legal_agent.interactions
    monkeypatch.setattr(legal_agent.interactions,"export_action",lambda *args:{"action":"generate","nonce":"test-export"})
    app.run()
    assert not app.exception
    assert set(app.session_state["exports"])=={"report_docx","report_pdf"}
