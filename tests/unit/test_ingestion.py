from docx import Document

from soc_verifier.ingestion.docx import ingest_docx


def test_document_order_and_evidence_locators(tmp_path):
    path = tmp_path / "spec.docx"
    document = Document()
    document.add_heading("Reset", level=1)
    paragraph = document.add_paragraph()
    paragraph.add_run("System reset ")
    paragraph.add_run("clears pending interrupts.")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "RESET"
    table.cell(0, 1).text = "Active low"
    document.add_paragraph("Reset release is synchronized.")
    document.save(path)

    result = ingest_docx(path)
    assert [block.kind for block in result.blocks] == [
        "paragraph",
        "paragraph",
        "table_row",
        "paragraph",
    ]
    assert result.blocks[1].text == "System reset clears pending interrupts."
    assert result.blocks[2].text == "RESET | Active low"
    assert result.blocks[2].locator == "word/document.xml/body/*[3]/tr[1]"
    assert all(block.section == "Reset" for block in result.blocks)
    assert result.sha256 == ingest_docx(path).sha256
