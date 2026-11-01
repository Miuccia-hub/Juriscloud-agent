"""Create fictional submission fixtures and export QA samples; never call a model."""
from pathlib import Path
from io import BytesIO
from docx import Document
from docx.oxml.ns import qn
from tests.fixture_data import load_demo
from legal_agent.exports import report_sections,report_docx,report_pdf,revised_docx,embed_report_font

root=Path(__file__).resolve().parents[1]
out=root/"output";out.mkdir(exist_ok=True)
for name in ["T01_采购合同","T02_Technology"]:
    doc=Document()
    for style in [doc.styles["Normal"],doc.styles["Title"]]:
        style.font.name="Noto Sans SC"
        style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"),"Noto Sans SC")
    for i,line in enumerate((root/"examples"/(name+".txt")).read_text().splitlines()):
        doc.add_paragraph(line,"Title" if i==0 else "Normal")
    buf=BytesIO(); doc.save(buf)
    (root/"examples"/(name+".docx")).write_bytes(embed_report_font(buf.getvalue()))
main,settings,intake,report,choices=load_demo()
sections=report_sections(report,[],choices,settings)
(out/"sample-report.docx").write_bytes(report_docx(sections))
(out/"sample-report.pdf").write_bytes(report_pdf(sections))
choices[0].state="采纳"
(out/"sample-redline.docx").write_bytes(revised_docx(main,choices))
# The boundary-case source is a real text PDF rather than an OCR image.
text=(root/"examples"/"T03_双语合作.txt").read_text()
(root/"examples"/"T03_双语合作.pdf").write_bytes(report_pdf([("虚构测试合同 / Fictional test contract",text)]))
print("Created fictional fixtures and QA exports in examples/ and output/.")
