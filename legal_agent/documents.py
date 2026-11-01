from __future__ import annotations

from io import BytesIO
import re
import zipfile
from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader
from .models import Clause, Material

MAX_BYTES = 8 * 1024 * 1024
MAX_CHARS = 60_000
MAX_SUPPLEMENTS = 6


def extract(name: str, data: bytes, doc_id="D1", role="主合同") -> Material:
    if not data or len(data) > MAX_BYTES:
        raise ValueError("文件为空或超过 8 MB。请拆分或转换后上传。")
    suffix = name.lower().rsplit(".", 1)[-1]
    warnings, clauses = [], []
    if suffix == "docx":
        try:
            with zipfile.ZipFile(BytesIO(data)) as z:
                if sum(i.file_size for i in z.infolist()) > 40 * 1024 * 1024:
                    raise ValueError("DOCX 解压后过大，无法安全解析。")
                xml = z.read("word/document.xml")
            if b"<!DOCTYPE" in xml:
                raise ValueError("不支持包含外部声明的文档。")
            doc = Document(BytesIO(data))
        except (zipfile.BadZipFile, KeyError) as exc:
            raise ValueError("这不是有效的 DOCX 文件。") from exc
        root = doc._element
        if root.xpath(".//w:ins | .//w:del | .//w:moveFrom | .//w:moveTo"):
            raise ValueError("原文件已有修订。请先在 Word 中处理修订并保存副本再上传，避免覆盖既有记录。")
        if root.xpath(".//w:txbxContent | .//w:object | .//w:altChunk"):
            raise ValueError("检测到文本框或嵌入对象。请转换为普通段落或文本 PDF，以免遗漏内容。")
        all_p = list(root.body.iter(qn("w:p")))
        for index, p in enumerate(all_p):
            text = "".join((node.text or "") if node.tag == qn("w:t") else "\t" if node.tag == qn("w:tab") else "\n"
                           for node in p.iter() if node.tag in (qn("w:t"),qn("w:tab"),qn("w:br"),qn("w:cr")))
            if text.strip():
                in_table = any(a.tag == qn("w:tc") for a in p.iterancestors())
                clauses.append(Clause(f"{doc_id}-P{index+1}", text, f"{'表格内' if in_table else ''}段落 {index+1}", index))
        if root.xpath(".//w:hyperlink | .//w:fldSimple | .//w:instrText"):
            warnings.append("含超链接或域的段落可阅读，自动写入修订时将拒绝复杂片段。")
        if doc.sections:
            for section in doc.sections:
                for label, part in [("页眉", section.header), ("页脚", section.footer)]:
                    for p in part.paragraphs:
                        if p.text.strip():
                            clauses.append(Clause(f"{doc_id}-H{len(clauses)+1}", p.text, label))
    elif suffix == "pdf":
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("不支持加密 PDF，请先提供未加密副本。")
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if len(text.strip()) < 12:
                raise ValueError(f"第 {i+1} 页缺少可读文本，可能是扫描件；首版不支持 OCR。")
            for j, block in enumerate(re.split(r"\n\s*\n", text)):
                if block.strip():
                    clauses.append(Clause(f"{doc_id}-P{i+1}-{j+1}", block.strip(), f"PDF 第 {i+1} 页 / 片段 {j+1}"))
        warnings.append("PDF 会重新生成 Word 排版，不能保留原 PDF 版式。")
    elif suffix == "txt":
        text = data.decode("utf-8-sig")
        for i, line in enumerate(text.splitlines()):
            if line.strip():
                clauses.append(Clause(f"{doc_id}-P{i+1}", line, f"文本第 {i+1} 行"))
        warnings.append("文本输入将使用标准 Word 排版。")
    else:
        raise ValueError("支持 DOCX、文本 PDF 和 UTF-8 TXT；不支持 .doc 或扫描件。")
    if not clauses:
        raise ValueError("没有识别到正文。")
    if sum(len(c.text) for c in clauses) > MAX_CHARS:
        raise ValueError("材料超过 60,000 字符，请缩小本次材料范围；系统未截断正文。")
    return Material(doc_id, name, role, clauses, data, suffix, warnings)


def validate_bundle(main: Material, supplements: list[Material]):
    if len(supplements) > MAX_SUPPLEMENTS:
        raise ValueError("最多上传六份补充材料。")
    if sum(len(m.text) for m in [main, *supplements]) > MAX_CHARS:
        raise ValueError("全部材料合计超过 60,000 字符。请减少材料，系统未截断内容。")


def bundle_text(main: Material, supplements: list[Material]):
    return "\n\n".join(f"DOCUMENT {m.id} | {m.name} | ROLE {m.role}\n{m.text}" for m in [main, *supplements])
