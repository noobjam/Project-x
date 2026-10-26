"""Extract ordered paragraphs/table rows with locators into the original OOXML."""

from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from lxml.etree import _Element

from soc_verifier.domain.models import SourceBlock, Specification


def ingest_docx(path: Path) -> Specification:
    document = Document(str(path))
    blocks: list[SourceBlock] = []
    section = "Document"
    warnings: list[str] = []
    for element, locator, identifier in _body_blocks(
        document.element.body, "word/document.xml/body", "", warnings
    ):
        if element.tag == qn("w:p"):
            text = _text(element)
            style = element.find("./" + qn("w:pPr") + "/" + qn("w:pStyle"))
            if style is not None:
                name = style.get(qn("w:val"), "")
                if name.lower().startswith("heading") and text:
                    section = text
            if text:
                blocks.append(
                    SourceBlock(
                        id=f"P{identifier}",
                        kind="paragraph",
                        section=section,
                        locator=locator,
                        text=text,
                    )
                )
        elif element.tag == qn("w:tbl"):
            if element.findall(".//" + qn("w:sdt")):
                warnings.append(
                    f"Table content controls require manual extraction review: {locator}"
                )
            for row_index, row in enumerate(element.findall(qn("w:tr")), start=1):
                cells = [_text(cell) for cell in row.findall(qn("w:tc"))]
                if any(cells):
                    blocks.append(
                        SourceBlock(
                            id=f"T{identifier}-R{row_index:04d}",
                            kind="table_row",
                            section=section,
                            locator=f"{locator}/tr[{row_index}]",
                            text=" | ".join(cells),
                        )
                    )

    with ZipFile(path) as archive:
        names = archive.namelist()
        images = sum(name.startswith("word/media/") and not name.endswith("/") for name in names)
        if images:
            warnings.append(f"{images} embedded media files require visual interpretation")
        if "word/comments.xml" in names:
            warnings.append("Document comments are not included in this extraction")
        if any("word/header" in name or "word/footer" in name for name in names):
            warnings.append("Headers and footers are not included in this extraction")
        if "word/footnotes.xml" in names or "word/endnotes.xml" in names:
            warnings.append("Footnotes/endnotes are not included in this extraction")
    if document.element.body.findall(".//" + qn("w:txbxContent")):
        warnings.append("Text box layout/reading order requires manual review")
    if document.element.body.findall(".//" + qn("w:ins")) or document.element.body.findall(
        ".//" + qn("w:del")
    ):
        warnings.append("Tracked changes exist; the accepted revision must be confirmed")
    return Specification(
        document_name=path.name,
        sha256=sha256(path.read_bytes()).hexdigest(),
        blocks=blocks,
        extraction_warnings=warnings,
    )


def _body_blocks(
    parent: _Element, locator: str, prefix: str, warnings: list[str]
) -> Iterator[tuple[_Element, str, str]]:
    """Unwrap body-level content controls without losing original XML locations."""
    ignored = {
        qn(f"w:{tag}")
        for tag in (
            "sectPr",
            "bookmarkStart",
            "bookmarkEnd",
            "proofErr",
            "permStart",
            "permEnd",
            "commentRangeStart",
            "commentRangeEnd",
            "del",
            "moveFrom",
            "customXmlPr",
        )
    }
    for index, element in enumerate(parent, start=1):
        location = f"{locator}/*[{index}]"
        identifier = f"{prefix}{index:05d}"
        if element.tag in {qn("w:p"), qn("w:tbl")}:
            yield element, location, identifier
        elif element.tag == qn("w:sdt"):
            content = element.find(qn("w:sdtContent"))
            if content is not None:
                yield from _body_blocks(
                    content, f"{location}/sdtContent", f"{identifier}-C", warnings
                )
        elif element.tag in {qn("w:customXml"), qn("w:ins"), qn("w:moveTo")}:
            yield from _body_blocks(element, location, f"{identifier}-W", warnings)
        elif element.tag not in ignored:
            tag = str(element.tag).rsplit("}", 1)[-1]
            warnings.append(f"Unsupported body element {tag} was not extracted: {location}")


def _text(element: _Element) -> str:
    # Read text nodes rather than itertext(), which can duplicate python-docx run text.
    paragraphs = element.findall(".//" + qn("w:p"))
    if not paragraphs:
        paragraphs = [element]
    separators = {
        qn("w:tab"): "\t",
        qn("w:br"): "\n",
        qn("w:cr"): "\n",
        qn("w:noBreakHyphen"): "\u2011",
        qn("w:softHyphen"): "\u00ad",
    }
    return "\n".join(
        "".join(
            node.text or "" if node.tag == qn("w:t") else separators.get(str(node.tag), "")
            for node in paragraph.iter()
        )
        for paragraph in paragraphs
    ).strip()
