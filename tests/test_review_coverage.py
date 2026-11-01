"""Structural coverage regressions, with explicit test doubles, not legal accuracy claims."""
import pytest
from legal_agent.coverage import checklist,topic_payload,normalise_checks,attach_checks
from legal_agent.models import CoverageCheck,CoverageQuote,Risk,ReviewBatch,OmissionAudit,ReviewSynthesis,Report,CheckLink
from legal_agent.documents import extract
from tests.fixture_data import load_demo
from tests.test_core import FakeGateway
from legal_agent.workflow import Workflow
from legal_agent.exports import report_sections
from legal_agent.presentation import coverage_table


def row(id='E04',**changes):
    values=dict(check_id=id,status='未找到明确约定',assessment='Test-only missing arrangement.',quotes=[],concern=True,priority='中',next_step='Obtain the referenced policy and clarify the arrangement in writing.')
    values.update(changes)
    return CoverageCheck(**values)


@pytest.mark.parametrize('kind,key',[
    ('雇佣协议','employment'),('Executive employment agreement','employment'),('采购合同','procurement'),
    ('咨询服务协议','services'),('技术开发合同','development'),('保密协议','confidentiality'),
    ('知识产权许可协议','ip'),('合作合同','collaboration'),('财税服务合同','finance'),
])
def test_contract_type_selects_specialist_topics(kind,key):
    topics,profiles=checklist(kind)
    assert key in profiles
    assert len(topics)>10 and len({t.id for t in topics})==len(topics)


def test_unknown_type_is_general_only_not_silent_specialist_claim():
    topics,profiles=checklist('Unidentified bespoke arrangement')
    assert not profiles and len(topics)==10


@pytest.mark.parametrize('wording',['Annual leave: see policy.','Accrued but unused vacation will be paid.','Paid time off arrangements to be agreed.','年休假参照附件。'])
def test_leave_synonyms_and_indirect_mentions_are_candidates(wording):
    main=extract('test.txt',wording.encode())
    leave=next(t for t in checklist('employment')[0] if t.id=='E04')
    candidates=topic_payload([leave],main)[0]['candidate_clauses']
    assert candidates and candidates[0]['text']==wording
    # Keyword hints are not assigned a legal status by code.
    assert 'status' not in candidates[0]


def test_absence_of_keyword_match_does_not_automatically_become_missing_clause():
    main=extract('test.txt',b'Salary is paid monthly.')
    topic=next(t for t in checklist('employment')[0] if t.id=='E04')
    assert not topic_payload([topic],main)[0]['candidate_clauses']
    assert normalise_checks([], [topic],main)[0].status=='资料不足'


def test_missing_duplicate_and_invalid_quote_are_unresolved():
    main=extract('test.txt',b'Annual leave: see company policy.')
    topic=next(t for t in checklist('employment')[0] if t.id=='E04')
    assert normalise_checks([row(),row()], [topic],main)[0].status=='资料不足'
    bad=row(status='已分析',quotes=[CoverageQuote(clause_id=main.clauses[0].id,quote='Invented entitlement')])
    checked=normalise_checks([bad], [topic],main)[0]
    assert checked.status=='资料不足' and not checked.quotes
    valid=row(status='资料不足',quotes=[CoverageQuote(clause_id=main.clauses[0].id,quote=main.clauses[0].text)])
    assert normalise_checks([valid], [topic],main)[0].quotes


def test_three_headline_risks_cannot_hide_unmapped_leave_concern():
    main,settings,intake,report,_=load_demo()
    topics,_=checklist('employment')
    checks=normalise_checks([row()],topics,main)
    initial_count=len(report.risks)
    attach_checks(report,checks,topics,main,set(),[],True)
    assert len(report.risks)==initial_count+1
    assert any(r.id=='AUDIT-E04' for r in report.risks)
    assert len(report._review_checks)==len(topics)
    assert any('No recorded reading' in x for x in report.limitations)
    assert any('Full checklist' in title for title,_ in report_sections(report,[],[],settings))
    assert 'E04' not in str(Report.model_json_schema())  # Metadata never expands the provider schema.


def test_real_pipeline_retains_omission_even_when_synthesis_drops_it():
    main,settings,intake,initial,_=load_demo()
    intake.contract_type='employment agreement'
    class MissedLeaveGateway(FakeGateway):
        def structured(self,stage,schema,payload,instruction):
            result=super().structured(stage,schema,payload,instruction)
            if schema is OmissionAudit:
                return OmissionAudit(corrected_checks=[row()],missed_issues=['Obtain the missing leave policy.'],limitations=[])
            if schema is ReviewSynthesis:
                assert any(r['check_id']=='E04' and r['concern'] for r in payload['check_results'])
                assert 'documents' in payload and 'omission_audit' in payload
                return result # Only the original two test risks, no check links.
            return result
    report,*_=Workflow(MissedLeaveGateway()).review(main,[],settings,intake)
    assert len(report._review_checks)==17
    leave=next(r for r in report._review_checks if r['check_id']=='E04')
    assert leave['status']=='未找到明确约定'
    assert any(r.title=='年假及其他休假安排' for r in report.risks)
    assert 'Obtain the missing leave policy.' in report.next_steps
    assert all(r.verification=='待核实' for r in report.risks if r.title=='年假及其他休假安排')


def test_check_table_escapes_model_content():
    main=extract('test.txt',b'x')
    topic=next(t for t in checklist('employment')[0] if t.id=='E04')
    report=load_demo()[3]
    attach_checks(report,[row(assessment='<script>unsafe()</script>')],[topic],main,set(),[],True)
    table=coverage_table(report._review_checks)
    assert '<script>' not in table and '&lt;script&gt;' in table


def test_private_check_records_are_not_dropped_on_copy_or_export():
    main,settings,_,report,_=load_demo()
    topic=next(t for t in checklist('employment')[0] if t.id=='E04')
    attach_checks(report,[row()],[topic],main,set(),[],True)
    copied=report.model_copy(deep=True)
    assert copied._review_checks==report._review_checks
    assert '_review_checks' not in report.model_dump()
    assert any('E04' in title for title,_ in report_sections(copied,[],[],settings))


def test_unrelated_check_link_cannot_hide_missing_arrangement():
    main,_,_,report,_=load_demo()
    topic=next(t for t in checklist('employment')[0] if t.id=='E04')
    link=CheckLink(check_id='E04',risk_ids=[report.risks[0].id])
    attach_checks(report,[row()],[topic],main,set(),[link],True)
    assert any(r.id=='AUDIT-E04' for r in report.risks)


def test_added_provider_schemas_have_required_fields_and_no_private_metadata():
    for schema in (ReviewBatch,OmissionAudit,ReviewSynthesis):
        spec=schema.model_json_schema()
        nodes=[spec,*spec.get('$defs',{}).values()]
        for node in nodes:
            if node.get('type')=='object':
                assert set(node.get('required',[]))==set(node.get('properties',{}))
                assert node.get('additionalProperties') is False
                assert '_review_checks' not in node.get('properties',{})
