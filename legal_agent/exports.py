from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from uuid import uuid4
from lxml import etree
from xml.sax.saxutils import escape
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from .edits import accepted, check_conflicts
from .presentation import pkulaw_case_links_text


def embed_report_font(data):
    """Subset and embed the OFL font so Chinese DOCX text is portable."""
    from fontTools.ttLib import TTFont as Font
    from fontTools.subset import Subsetter, Options
    font_path=Path(__file__).resolve().parents[1]/"assets/fonts/NotoSansSC-Regular.ttf"
    with ZipFile(BytesIO(data)) as z:
        parts={n:z.read(n) for n in z.namelist()}
    root=etree.fromstring(parts["word/document.xml"])
    text="".join(root.itertext())
    font=Font(font_path)
    subset=Subsetter(options=Options()); subset.populate(text=text); subset.subset(font)
    raw=BytesIO(); font.save(raw)
    obfuscated=bytearray(raw.getvalue())
    identifier=uuid4()
    key=identifier.bytes[::-1]
    for i in range(min(32,len(obfuscated))): obfuscated[i]^=key[i%16]
    w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    pr="http://schemas.openxmlformats.org/package/2006/relationships"
    ct="http://schemas.openxmlformats.org/package/2006/content-types"
    table=etree.fromstring(parts["word/fontTable.xml"])
    record=next((item for item in table if item.get(f"{{{w}}}name")=="Noto Sans SC"),None)
    if record is None:
        record=etree.SubElement(table,f"{{{w}}}font",{f"{{{w}}}name":"Noto Sans SC"})
    for old in list(record.findall(f"{{{w}}}embedRegular")):
        record.remove(old)
    relationship_id="rIdJuriscloud"+identifier.hex
    font_part="fonts/Juriscloud-"+identifier.hex+".odttf"
    etree.SubElement(record,f"{{{w}}}embedRegular",{f"{{{r}}}id":relationship_id,f"{{{w}}}fontKey":"{"+str(identifier).upper()+"}",f"{{{w}}}subsetted":"true"})
    parts["word/fontTable.xml"]=etree.tostring(table,xml_declaration=True,encoding="UTF-8",standalone=True)
    relpath="word/_rels/fontTable.xml.rels"
    rels=etree.fromstring(parts[relpath]) if relpath in parts else etree.Element(f"{{{pr}}}Relationships",nsmap={None:pr})
    etree.SubElement(rels,f"{{{pr}}}Relationship",Id=relationship_id,Type=r+"/font",Target=font_part)
    parts[relpath]=etree.tostring(rels,xml_declaration=True,encoding="UTF-8",standalone=True)
    types=etree.fromstring(parts["[Content_Types].xml"])
    etree.SubElement(types,f"{{{ct}}}Override",PartName="/word/"+font_part,ContentType="application/vnd.openxmlformats-officedocument.obfuscatedFont")
    parts["[Content_Types].xml"]=etree.tostring(types,xml_declaration=True,encoding="UTF-8",standalone=True)
    parts["word/"+font_part]=bytes(obfuscated)
    out=BytesIO()
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        for name,content in parts.items(): z.writestr(name,content)
    return out.getvalue()


def report_sections(report,sources,choices,settings,answers=()):
    sections = [("商业合同审查报告 / Contract review", report.summary),
                ("审查设置 / Scope", f"{settings.jurisdiction} · {settings.stance} · {settings.mode} · {settings.language}\n{settings.focus}"),
                ("覆盖 / Coverage", "\n".join(report.coverage)),
                ("假设 / Assumptions", "\n".join(report.assumptions))]
    links=pkulaw_case_links_text(report,sources)
    if links: sections.append(("北大法宝案例链接 / PKULAW case links",links))
    checks=getattr(report,"_review_checks",[])
    if checks:
        sections.append(("完整检查清单 / Full checklist","检查记录为模型判断，不能作为独立合规保证。 / Model check records are not independent compliance assurance."))
        for row in checks:
            sections.append((row['check_id']+" · "+row['topic'],row['status']+"\n"+row['assessment']+"\n"+
                "\n".join(q['clause_id']+": "+q['quote'] for q in row['quotes'])+"\n"+row['next_step']))
    for r in report.risks:
        sections.append((f"{r.id} · {r.title}",f"{r.severity} / {r.category} / {r.action}\n位置：{', '.join(r.clause_ids)}\n"
                         f"{r.explanation}\n影响：{r.impact}\n核验：{r.verification}\n来源：{', '.join(r.source_ids) or '无 / none'}\n"
                         + "\n".join(r.missing_facts)))
    for question,answer in answers:
        sections.append(("条款追问 / Follow-up", question + "\n\n" + answer.summary))
        links=pkulaw_case_links_text(answer,sources)
        if links: sections.append(("北大法宝案例链接 / PKULAW case links",links))
        for r in answer.risks:
            sections.append((r.title, f"{r.severity} · {r.verification}\n{r.explanation}\n{', '.join(r.source_ids)}"))
        sections.append(("追问限制 / Follow-up limits", "\n".join(answer.limitations)))
    for c in choices:
        sections.append((f"修改 {c.edit.id} / {c.state}", f"位置：{c.edit.clause_id}\n原文：{c.edit.original}\n"
                         f"建议：{c.replacement}\n理由：{c.edit.reason}\n{c.edit.bilingual_note}\n"
                         f"来源：{', '.join(c.edit.source_ids)}\n重新确认：{c.needs_reconfirmation}"))
    for s in sources:
        sections.append((f"{s.id} · {s.title}",f"{s.status}\n{s.url}\n{s.retrieved_at}\n{s.warning}"))
    sections += [("后续行动 / Next steps","\n".join(report.next_steps)),
                 ("限制 / Limitations","\n".join(dict.fromkeys(report.limitations))),
                 ("工具说明 / Notice","AI 辅助审查，非全面合规保证。引用、适用法律及修改文本需专业人员复核。\nAI-assisted review; professional verification remains required.")]
    return sections


def report_docx(sections):
    doc = Document()
    for name in ["Normal", "Title", "Heading 1", "Heading 2"]:
        style = doc.styles[name]
        style.font.name = "Noto Sans SC"
        style.font.color.rgb = RGBColor(0,0,0)
        style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"),"Noto Sans SC")
        # Word's default template can carry an ornamental title border.
        for borders in style.element.xpath(".//w:pBdr"):
            borders.getparent().remove(borders)
    doc.styles["Normal"].font.size = Pt(10.5)
    for i,(title,body) in enumerate(sections):
        doc.add_paragraph(title, "Title" if i == 0 else "Heading 1")
        for line in body.splitlines():
            if line.strip():
                doc.add_paragraph(line)
    buf = BytesIO()
    doc.save(buf)
    return embed_report_font(buf.getvalue())


def report_pdf(sections):
    if "JuriscloudCJK" not in pdfmetrics.getRegisteredFontNames():
        font_path=Path(__file__).resolve().parents[1]/"assets/fonts/NotoSansSC-Regular.ttf"
        pdfmetrics.registerFont(TTFont("JuriscloudCJK",str(font_path)))
    body = ParagraphStyle("Body",fontName="JuriscloudCJK",fontSize=10,leading=16,wordWrap="CJK",spaceAfter=7)
    heading = ParagraphStyle("Heading",parent=body,fontSize=14,leading=20,textColor=colors.HexColor("#17365F"),spaceBefore=12,keepWithNext=True)
    buf = BytesIO()
    story = []
    for title,text in sections:
        story.append(Paragraph(escape(title),heading))
        # Separate long paragraphs to avoid an unbreakable page-sized block.
        for line in text.splitlines():
            if line.strip():
                story.append(Paragraph(escape(line),body))
        story.append(Spacer(1,5))
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=45,leftMargin=45,topMargin=40,bottomMargin=40).build(story)
    return buf.getvalue()


def _run(text,properties=None,deleted=False):
    r = OxmlElement("w:r")
    if properties is not None:
        r.append(deepcopy(properties))
    t = OxmlElement("w:delText" if deleted else "w:t")
    t.set(qn("xml:space"),"preserve")
    t.text = text
    r.append(t)
    return r


def revised_docx(main,choices):
    errors = check_conflicts(main,choices)
    if errors:
        raise ValueError("；".join(errors))
    if not accepted(choices):
        raise ValueError("请先采纳至少一项修改。")
    if main.kind == "docx":
        doc = Document(BytesIO(main.data))
        paragraphs = list(doc._element.body.iter(qn("w:p")))
        mapping = {c.id:paragraphs[c.paragraph_index] for c in main.clauses if c.paragraph_index is not None}
    else:
        doc = Document()
        doc.styles["Normal"].font.name="Noto Sans SC"
        doc.styles["Normal"].element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"),"Noto Sans SC")
        mapping = {c.id:doc.add_paragraph(c.text)._p for c in main.clauses}
    group = {}
    for choice in accepted(choices):
        group.setdefault(choice.edit.clause_id,[]).append(choice)
    serial, stamp = 1, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for clause_id,items in group.items():
        p = mapping.get(clause_id)
        if p is None:
            raise ValueError(f"{clause_id} 是页眉、页脚或无法定位的内容，请人工处理。")
        if any(child.tag not in (qn("w:pPr"),qn("w:r")) for child in p):
            raise ValueError(f"{clause_id} 包含超链接、书签或复杂域，已停止导出以保护原文件。")
        spans,position = [],0
        for r in p.findall(qn("w:r")):
            if any(child.tag not in (qn("w:rPr"),qn("w:t")) for child in r):
                raise ValueError(f"{clause_id} 含域、图片或特殊字符结构，请人工处理。")
            text = "".join(r.xpath("./w:t/text()"))
            spans.append((position,position+len(text),r.find(qn("w:rPr"))))
            position += len(text)
        original = "".join(p.xpath("./w:r/w:t/text()"))
        clause = next(c for c in main.clauses if c.id == clause_id)
        if original != clause.text:
            raise ValueError(f"{clause_id} 原文校验失败，未写入修订。")
        def fragments(start,end,deleted=False):
            return [_run(original[max(start,a):min(end,b)],pr,deleted) for a,b,pr in spans if max(start,a)<min(end,b)]
        for r in list(p.findall(qn("w:r"))):
            p.remove(r)
        cursor = 0
        for item in sorted(items,key=lambda x:original.index(x.edit.original)):
            start = original.index(item.edit.original)
            end = start + len(item.edit.original)
            for r in fragments(cursor,start):
                p.append(r)
            for tag,text,deleted in [("w:del",original[start:end],True),("w:ins",item.replacement,False)]:
                if not text:
                    continue
                change = OxmlElement(tag)
                change.set(qn("w:id"),str(serial)); serial += 1
                change.set(qn("w:author"),"Juriscloud review")
                change.set(qn("w:date"),stamp)
                if deleted:
                    for r in fragments(start,end,True):
                        change.append(r)
                else:
                    pr = next((pr for a,b,pr in spans if a <= start < b),None)
                    change.append(_run(text,pr))
                p.append(change)
            cursor = end
        for r in fragments(cursor,len(original)):
            p.append(r)
    if doc.settings.element.find(qn("w:trackRevisions")) is None:
        doc.settings.element.append(OxmlElement("w:trackRevisions"))
    buf=BytesIO(); doc.save(buf)
    return embed_report_font(buf.getvalue())
