"""Integration tests for the complete attachment processing workflow."""

import pytest
from pathlib import Path
import tempfile
import os
import csv

from email_tool.attachment_types import AttachmentType, get_attachment_type
from email_tool.attachment_parsers.pdf import PDFAttachmentParser
from email_tool.attachment_parsers.office import OfficeAttachmentParser
from email_tool.attachment_parsers.text import TextAttachmentParser
from email_tool.attachment_parsers.base import ParsedAttachment, AttachmentMetadata


class TestCompleteAttachmentWorkflow:
    """Integration tests for complete attachment processing workflow."""

    @pytest.fixture
    def parsers(self):
        """Create all parsers for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield {
                "pdf": PDFAttachmentParser(tmpdir),
                "office": OfficeAttachmentParser(tmpdir),
                "text": TextAttachmentParser(tmpdir),
            }

    def test_pdf_attachment_workflow(self, parsers):
        """Test complete PDF attachment processing workflow."""
        parser = parsers["pdf"]
        
        # Create a test PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            # Write a minimal PDF header (not a real PDF, but tests error handling)
            tmp.write(b"%PDF-1.4\n")
            tmp.write(b"1 0 obj\n<< /Type /Catalog >>\nendobj\n")
            tmp.write(b"xref\n0 2\n0000000000 65535 f \n0000000009 00000 n \n")
            tmp.write(b"trailer\n<< /Size 2 /Root 1 0 R >>\n")
            tmp.write(b"startxref\n50\n%%EOF")
            tmp_path = Path(tmp.name)

        try:
            # Test type detection
            attachment_type = get_attachment_type(filename="test.pdf")
            assert attachment_type == AttachmentType.PDF

            # Test metadata extraction
            metadata = parser.extract_metadata(tmp_path)
            assert metadata.parser_name == "PDFAttachmentParser"
            assert metadata.attachment_type == AttachmentType.PDF
            assert metadata.original_filename == tmp_path.name

            # Test text extraction
            result = parser.extract_text(
                tmp_path, "attachment-123", "email-456"
            )
            assert result.attachment_type == AttachmentType.PDF
            assert result.attachment_id == "attachment-123"
            assert result.email_id == "email-456"
            assert result.original_filename == tmp_path.name
            
            # Should handle error gracefully for invalid PDF
            assert result.success is False
            assert result.error_message is not None

        finally:
            os.unlink(tmp_path)

    def test_docx_attachment_workflow(self, parsers):
        """Test complete DOCX attachment processing workflow."""
        parser = parsers["office"]
        
        # Create a minimal DOCX file (ZIP archive with XML content)
        import zipfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            
            # Create a minimal DOCX structure
            with zipfile.ZipFile(tmp_path, 'w') as docx:
                # Document main XML
                docx.writestr("docProps/app.xml", 
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">')
                
                # Document content
                docx.writestr("word/document.xml",
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:body><w:p><w:r><w:t>Test Document Content</w:t></w:r></w:p></w:body></w:document>')
                
                # Relationships
                docx.writestr("_rels/.rels",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">')
                
                # Word relationships
                docx.writestr("word/_rels/document.xml.rels",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">')
                
                # Content types
                docx.writestr("[Content_Types].xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">')
            
            try:
                # Test type detection
                attachment_type = get_attachment_type(filename="test.docx")
                assert attachment_type == AttachmentType.DOCX

                # Test metadata extraction
                metadata = parser.extract_metadata(tmp_path)
                assert metadata.parser_name == "OfficeAttachmentParser"
                assert metadata.attachment_type == AttachmentType.DOCX
                assert metadata.original_filename == tmp_path.name

                # Test text extraction
                result = parser.extract_text(
                    tmp_path, "attachment-456", "email-789"
                )
                assert result.attachment_type == AttachmentType.DOCX
                assert result.attachment_id == "attachment-456"
                assert result.email_id == "email-789"
                assert result.original_filename == tmp_path.name

            finally:
                os.unlink(tmp_path)

    def test_xlsx_attachment_workflow(self, parsers):
        """Test complete XLSX attachment processing workflow."""
        parser = parsers["office"]
        
        # Create a minimal XLSX file
        import zipfile
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            
            # Create a minimal XLSX structure
            with zipfile.ZipFile(tmp_path, 'w') as xlsx:
                # Content types
                xlsx.writestr("[Content_Types].xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">')
                
                # Relationships
                xlsx.writestr("_rels/.rels",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">')
                
                # Workbook
                xlsx.writestr("xl/workbook.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
                
                # Worksheet
                xlsx.writestr("xl/worksheets/sheet1.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
                
                # Shared strings
                xlsx.writestr("xl/sharedStrings.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
            
            try:
                # Test type detection
                attachment_type = get_attachment_type(filename="test.xlsx")
                assert attachment_type == AttachmentType.XLSX

                # Test metadata extraction
                metadata = parser.extract_metadata(tmp_path)
                assert metadata.parser_name == "OfficeAttachmentParser"
                assert metadata.attachment_type == AttachmentType.XLSX
                assert metadata.original_filename == tmp_path.name

                # Test text extraction
                result = parser.extract_text(
                    tmp_path, "attachment-789", "email-012"
                )
                assert result.attachment_type == AttachmentType.XLSX
                assert result.attachment_id == "attachment-789"
                assert result.email_id == "email-012"
                assert result.original_filename == tmp_path.name

            finally:
                os.unlink(tmp_path)

    def test_txt_attachment_workflow(self, parsers):
        """Test complete TXT attachment processing workflow."""
        parser = parsers["text"]
        
        # Create a test TXT file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as tmp:
            tmp.write("This is a test text file.\n")
            tmp.write("It contains multiple lines.\n")
            tmp.write("Line 3 of the test content.\n")
            tmp_path = Path(tmp.name)

        try:
            # Test type detection
            attachment_type = get_attachment_type(filename="test.txt")
            assert attachment_type == AttachmentType.TXT

            # Test metadata extraction
            metadata = parser.extract_metadata(tmp_path)
            assert metadata.parser_name == "TextAttachmentParser"
            assert metadata.attachment_type == AttachmentType.TXT
            assert metadata.original_filename == tmp_path.name

            # Test text extraction
            result = parser.extract_text(
                tmp_path, "attachment-101", "email-202"
            )
            assert result.success is True
            assert result.attachment_type == AttachmentType.TXT
            assert result.attachment_id == "attachment-101"
            assert result.email_id == "email-202"
            assert result.original_filename == tmp_path.name
            assert "This is a test text file" in result.text_content
            assert "Line 3 of the test content" in result.text_content

        finally:
            os.unlink(tmp_path)

    def test_csv_attachment_workflow(self, parsers):
        """Test complete CSV attachment processing workflow."""
        parser = parsers["text"]
        
        # Create a test CSV file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w', newline='') as tmp:
            writer = csv.writer(tmp)
            writer.writerow(["Name", "Age", "City"])
            writer.writerow(["Alice", "30", "New York"])
            writer.writerow(["Bob", "25", "Los Angeles"])
            tmp_path = Path(tmp.name)

        try:
            # Test type detection
            attachment_type = get_attachment_type(filename="test.csv")
            assert attachment_type == AttachmentType.CSV

            # Test metadata extraction
            metadata = parser.extract_metadata(tmp_path)
            assert metadata.parser_name == "TextAttachmentParser"
            assert metadata.attachment_type == AttachmentType.CSV
            assert metadata.original_filename == tmp_path.name

            # Test text extraction
            result = parser.extract_text(
                tmp_path, "attachment-303", "email-404"
            )
            assert result.success is True
            assert result.attachment_type == AttachmentType.CSV
            assert "Name,Age,City" in result.text_content
            assert "Alice,30,New York" in result.text_content

        finally:
            os.unlink(tmp_path)

    def test_mixed_attachment_workflow(self, parsers):
        """Test processing multiple attachments of different types."""
        pdf_parser = parsers["pdf"]
        office_parser = parsers["office"]
        text_parser = parsers["text"]
        
        attachments = []
        
        # Create PDF attachment
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4\nTest PDF")
            pdf_path = Path(tmp.name)
        attachments.append(("pdf", pdf_path, pdf_parser))
        
        # Create DOCX attachment
        import zipfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            with zipfile.ZipFile(tmp_path, 'w') as docx:
                docx.writestr("word/document.xml",
                    '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:body><w:p><w:r><w:t>DOCX Content</w:t></w:r></w:p></w:body></w:document>')
                docx.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships></Relationships>')
                docx.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types></Types>')
                docx.writestr("word/_rels/document.xml.rels", '<?xml version="1.0"?><Relationships></Relationships>')
                docx.writestr("docProps/app.xml", '<?xml version="1.0"?><Properties></Properties>')
        attachments.append(("docx", tmp_path, office_parser))
        
        # Create TXT attachment
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as tmp:
            tmp.write("Text content")
            txt_path = Path(tmp.name)
        attachments.append(("txt", txt_path, text_parser))
        
        try:
            # Process all attachments
            results = []
            for att_type, path, parser in attachments:
                result = parser.extract_text(path, f"attachment-{att_type}", "email-123")
                results.append((att_type, result))
            
            # Verify all results
            assert len(results) == 3
            
            # PDF should fail (invalid PDF)
            pdf_result = next(r for r in results if r[0] == "pdf")
            assert pdf_result[1].attachment_type == AttachmentType.PDF
            
            # DOCX should succeed
            docx_result = next(r for r in results if r[0] == "docx")
            assert docx_result[1].success is True
            # DOCX text extraction may return None for minimal files
            # Just verify the result object is valid
            assert docx_result[1].attachment_type == AttachmentType.DOCX
            
            # TXT should succeed
            txt_result = next(r for r in results if r[0] == "txt")
            assert txt_result[1].success is True
            assert "Text content" in txt_result[1].text_content

        finally:
            for _, path, _ in attachments:
                os.unlink(path)

    def test_error_handling_workflow(self, parsers):
        """Test error handling in complete workflow."""
        parser = parsers["pdf"]
        
        # Test with non-existent file
        non_existent = Path("/non/existent/file.pdf")
        
        # Should handle error gracefully
        with pytest.raises(FileNotFoundError):
            parser.extract_text(non_existent, "attachment-999", "email-888")

    def test_metadata_extraction_workflow(self, parsers):
        """Test metadata extraction for all attachment types."""
        pdf_parser = parsers["pdf"]
        office_parser = parsers["office"]
        text_parser = parsers["text"]
        
        # Test PDF metadata
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4\nTest")
            pdf_path = Path(tmp.name)
        
        try:
            pdf_metadata = pdf_parser.extract_metadata(pdf_path)
            assert pdf_metadata.parser_name == "PDFAttachmentParser"
            assert pdf_metadata.attachment_type == AttachmentType.PDF
            assert pdf_metadata.original_filename == pdf_path.name
        finally:
            os.unlink(pdf_path)
        
        # Test DOCX metadata
        import zipfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            with zipfile.ZipFile(tmp_path, 'w') as docx:
                docx.writestr("word/document.xml", '<w:document></w:document>')
                docx.writestr("_rels/.rels", '<Relationships></Relationships>')
                docx.writestr("[Content_Types].xml", '<Types></Types>')
                docx.writestr("word/_rels/document.xml.rels", '<Relationships></Relationships>')
                docx.writestr("docProps/app.xml", '<Properties></Properties>')
        
        try:
            docx_metadata = office_parser.extract_metadata(tmp_path)
            assert docx_metadata.parser_name == "OfficeAttachmentParser"
            assert docx_metadata.attachment_type == AttachmentType.DOCX
            assert docx_metadata.original_filename == tmp_path.name
        finally:
            os.unlink(tmp_path)
        
        # Test TXT metadata
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode='w') as tmp:
            tmp.write("Test")
            txt_path = Path(tmp.name)
        
        try:
            txt_metadata = text_parser.extract_metadata(txt_path)
            assert txt_metadata.parser_name == "TextAttachmentParser"
            assert txt_metadata.attachment_type == AttachmentType.TXT
            assert txt_metadata.original_filename == txt_path.name
        finally:
            os.unlink(txt_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
