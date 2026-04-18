from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from app.schemas.rag import ParsedSection


class DocumentParserService:
    def __init__(self, converter: Any = None) -> None:
        if converter is None:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()

        self.converter = converter

    def parse_pdf(self, file_bytes: bytes, filename: str) -> list[ParsedSection]:
        if not file_bytes:
            raise ValueError("file_bytes must not be empty")
        if not filename or not filename.strip():
            raise ValueError("filename must not be blank")
        if Path(filename.strip()).suffix.lower() != ".pdf":
            raise ValueError("filename must end with .pdf")

        safe_filename = filename.strip()
        temp_path = None

        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            result = self.converter.convert(temp_path)
            markdown = result.document.export_to_markdown()
        finally:
            if temp_path is not None:
                temp_file_path = Path(temp_path)
                try:
                    if temp_file_path.exists():
                        temp_file_path.unlink()
                except FileNotFoundError:
                    pass

        return [
            ParsedSection(
                text=markdown,
                section_title=Path(safe_filename).stem,
                page_number=None,
            )
        ]
