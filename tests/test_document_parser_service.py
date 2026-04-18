from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.document_parser_service import DocumentParserService


@pytest.mark.parametrize(
    ("file_bytes", "filename", "message"),
    [
        (b"%PDF-1.4", "   ", "filename must not be blank"),
        (b"%PDF-1.4", "report.txt", "filename must end with .pdf"),
        (b"", "report.pdf", "file_bytes must not be empty"),
    ],
)
def test_parse_pdf_rejects_invalid_inputs_without_calling_converter(
    file_bytes: bytes, filename: str, message: str
) -> None:
    converter = MagicMock()
    service = DocumentParserService(converter=converter)

    with pytest.raises(ValueError, match=message):
        service.parse_pdf(file_bytes, filename)

    converter.convert.assert_not_called()


def test_parse_pdf_returns_markdown_section() -> None:
    fake_result = SimpleNamespace(
        document=SimpleNamespace(
            export_to_markdown=MagicMock(return_value="# Revenue Report\n\n| Year | Revenue |")
        )
    )
    converter = MagicMock()
    converter.convert.return_value = fake_result

    sections = DocumentParserService(converter=converter).parse_pdf(b"%PDF-1.4", "report.pdf")

    assert len(sections) == 1
    assert sections[0].section_title == "report"
    assert "Revenue" in sections[0].text

    temp_path = Path(converter.convert.call_args.args[0])
    assert temp_path.suffix == ".pdf"


def test_parse_pdf_removes_temp_file_after_successful_conversion() -> None:
    fake_result = SimpleNamespace(
        document=SimpleNamespace(export_to_markdown=MagicMock(return_value="# Parsed"))
    )
    converter = MagicMock()
    converter.convert.return_value = fake_result

    sections = DocumentParserService(converter=converter).parse_pdf(b"%PDF-1.4", "report.pdf")

    assert len(sections) == 1
    temp_path = Path(converter.convert.call_args.args[0])
    assert not temp_path.exists()


def test_parse_pdf_removes_temp_file_when_conversion_fails() -> None:
    converter = MagicMock()
    converter.convert.side_effect = RuntimeError("conversion failed")
    service = DocumentParserService(converter=converter)

    with pytest.raises(RuntimeError, match="conversion failed"):
        service.parse_pdf(b"%PDF-1.4", "broken.pdf")

    temp_path = Path(converter.convert.call_args.args[0])
    assert not temp_path.exists()


def test_parse_pdf_removes_temp_file_when_markdown_export_fails() -> None:
    fake_result = SimpleNamespace(
        document=SimpleNamespace(
            export_to_markdown=MagicMock(side_effect=RuntimeError("markdown export failed"))
        )
    )
    converter = MagicMock()
    converter.convert.return_value = fake_result
    service = DocumentParserService(converter=converter)

    with pytest.raises(RuntimeError, match="markdown export failed"):
        service.parse_pdf(b"%PDF-1.4", "broken.pdf")

    temp_path = Path(converter.convert.call_args.args[0])
    assert not temp_path.exists()
