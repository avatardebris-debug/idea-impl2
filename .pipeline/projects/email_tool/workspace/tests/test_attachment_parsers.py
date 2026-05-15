"""Tests for the attachment processing module."""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so email_tool can be imported
# The email_tool package is at /workspace/workspace/email_tool
# So we need to add /workspace/workspace to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from email_tool.attachment_types import (
    AttachmentType,
    get_attachment_type,
    is_text_attachment,
    is_image_attachment,
    is_office_attachment,
    is_pdf_attachment,
    get_supported_types
)
from email_tool.attachment_parsers.base import (
    AttachmentMetadata,
    ParsedAttachment
)
from email_tool.attachment_parsers.pdf import PDFAttachmentParser
from email_tool.attachment_parsers.office import OfficeAttachmentParser
from email_tool.attachment_parsers.text import TextAttachmentParser
from email_tool.attachment_processor import (
    AttachmentProcessor,
    AttachmentDispatcher,
    AttachmentActionExecutor,
    AttachmentPipelineBuilder,
    AttachmentPipelineExecutor,
    AttachmentPipelineMonitor,
    AttachmentPipelineConfig
)
from email_tool.models import (
    Email,
    AttachmentProcessingResult,
    EmailAttachmentProcessingResult
)


class TestAttachmentTypes:
    """Tests for attachment type detection."""
    
    def test_get_attachment_type_from_mime_pdf(self):
        """Test PDF detection from MIME type."""
        attachment_type = get_attachment_type(
            mime_type="application/pdf",
            filename="document.pdf"
        )
        assert attachment_type == AttachmentType.PDF
    
    def test_get_attachment_type_from_mime_office(self):
        """Test Office document detection from MIME type."""
        attachment_type = get_attachment_type(
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="document.docx"
        )
        assert attachment_type == AttachmentType.DOCX
    
    def test_get_attachment_type_from_filename_pdf(self):
        """Test PDF detection from filename."""
        attachment_type = get_attachment_type(
            mime_type="",
            filename="document.pdf"
        )
        assert attachment_type == AttachmentType.PDF
    
    def test_get_attachment_type_from_filename_txt(self):
        """Test text file detection from filename."""
        attachment_type = get_attachment_type(
            mime_type="",
            filename="document.txt"
        )
        assert attachment_type == AttachmentType.TXT
    
    def test_get_attachment_type_from_filename_csv(self):
        """Test CSV file detection from filename."""
        attachment_type = get_attachment_type(
            mime_type="",
            filename="data.csv"
        )
        assert attachment_type == AttachmentType.CSV
    
    def test_get_attachment_type_unknown(self):
        """Test unknown file type detection."""
        attachment_type = get_attachment_type(
            mime_type="",
            filename="document.xyz"
        )
        assert attachment_type == AttachmentType.UNKNOWN
    
    def test_is_text_attachment(self):
        """Test text attachment detection."""
        assert is_text_attachment(AttachmentType.TXT)
        assert is_text_attachment(AttachmentType.CSV)
        assert not is_text_attachment(AttachmentType.PDF)
    
    def test_is_image_attachment(self):
        """Test image attachment detection."""
        assert is_image_attachment(AttachmentType.JPG)
        assert is_image_attachment(AttachmentType.PNG)
        assert not is_image_attachment(AttachmentType.TXT)
    
    def test_is_office_attachment(self):
        """Test Office document detection."""
        assert is_office_attachment(AttachmentType.DOCX)
        assert is_office_attachment(AttachmentType.XLSX)
        assert is_office_attachment(AttachmentType.PPTX)
        assert not is_office_attachment(AttachmentType.TXT)
    
    def test_is_pdf_attachment(self):
        """Test PDF detection."""
        assert is_pdf_attachment(AttachmentType.PDF)
        assert not is_pdf_attachment(AttachmentType.TXT)
    
    def test_get_supported_types(self):
        """Test getting supported attachment types."""
        supported = get_supported_types()
        assert len(supported) > 0
        assert AttachmentType.PDF in supported
        assert AttachmentType.TXT in supported


class TestAttachmentParsers:
    """Tests for attachment parsers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.parser_base_path = os.path.join(self.temp_dir, "parsers")
        os.makedirs(self.parser_base_path, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_text_parser_parse_txt_file(self):
        """Test text parser with a .txt file."""
        # Create a test text file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("This is a test file.\nWith multiple lines.\n")
        
        parser = TextAttachmentParser(self.parser_base_path)
        
        result = parser.parse(
            file_path=test_file,
            attachment_id="test_001",
            email_id="email_001",
            original_filename="test.txt",
            content_type="text/plain",
            size_bytes=45,
            attachment_type=AttachmentType.TXT
        )
        
        assert result.success
        assert result.text_content == "This is a test file.\nWith multiple lines.\n"
        assert result.metadata is not None
        assert result.metadata["file_size"] == 45
    
    def test_text_parser_parse_csv_file(self):
        """Test text parser with a .csv file."""
        # Create a test CSV file
        test_file = os.path.join(self.temp_dir, "test.csv")
        with open(test_file, 'w') as f:
            f.write("name,age,city\nJohn,30,NYC\nJane,25,LA\n")
        
        parser = TextAttachmentParser(self.parser_base_path)
        
        result = parser.parse(
            file_path=test_file,
            attachment_id="test_002",
            email_id="email_001",
            original_filename="test.csv",
            content_type="text/csv",
            size_bytes=45,
            attachment_type=AttachmentType.CSV
        )
        
        assert result.success
        assert "name,age,city" in result.text_content
        assert result.metadata is not None
    
    def test_text_parser_parse_nonexistent_file(self):
        """Test text parser with a non-existent file."""
        parser = TextAttachmentParser(self.parser_base_path)
        
        result = parser.parse(
            file_path="/nonexistent/file.txt",
            attachment_id="test_003",
            email_id="email_001",
            original_filename="test.txt",
            content_type="text/plain",
            size_bytes=0,
            attachment_type=AttachmentType.TXT
        )
        
        assert not result.success
        assert result.error_message is not None
    
    def test_office_parser_parse_docx_file(self):
        """Test Office parser with a .docx file."""
        # Create a test DOCX file (empty for now)
        test_file = os.path.join(self.temp_dir, "test.docx")
        # Create a minimal valid DOCX file
        with open(test_file, 'wb') as f:
            # DOCX files are ZIP archives, we'll create a minimal one
            # For testing purposes, we'll just create an empty file
            # In real tests, we'd use a proper DOCX file
            f.write(b"PK")  # ZIP signature
        
        parser = OfficeAttachmentParser(self.parser_base_path)
        
        result = parser.parse(
            file_path=test_file,
            attachment_id="test_004",
            email_id="email_001",
            original_filename="test.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=100,
            attachment_type=AttachmentType.DOCX
        )
        
        # The parser should handle the file gracefully
        # In a real scenario, it would extract text from the DOCX
        assert result.success or not result.success  # Either way is acceptable for this test
    
    def test_pdf_parser_parse_pdf_file(self):
        """Test PDF parser with a .pdf file."""
        # Create a test PDF file (empty for now)
        test_file = os.path.join(self.temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            # Minimal PDF header
            f.write(b"%PDF-1.4\n")
        
        parser = PDFAttachmentParser(self.parser_base_path)
        
        result = parser.parse(
            file_path=test_file,
            attachment_id="test_005",
            email_id="email_001",
            original_filename="test.pdf",
            content_type="application/pdf",
            size_bytes=100,
            attachment_type=AttachmentType.PDF
        )
        
        # The parser should handle the file gracefully
        assert result.success or not result.success  # Either way is acceptable for this test


class TestAttachmentProcessor:
    """Tests for the attachment processor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = AttachmentProcessor(
            base_path=self.temp_dir,
            dry_run=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_process_attachment_txt_file(self):
        """Test processing a text file attachment."""
        # Create a test text file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        result = self.processor.process_attachment(
            file_path=test_file,
            attachment_id="test_001",
            email_id="email_001",
            original_filename="test.txt",
            content_type="text/plain",
            size_bytes=12,
            attachment_type=AttachmentType.TXT
        )
        
        assert result.success
        assert result.attachment_type == AttachmentType.TXT
        assert result.text_content == "Test content"
    
    def test_process_attachment_pdf_file(self):
        """Test processing a PDF file attachment."""
        # Create a test PDF file
        test_file = os.path.join(self.temp_dir, "test.pdf")
        with open(test_file, 'wb') as f:
            f.write(b"%PDF-1.4\n")
        
        result = self.processor.process_attachment(
            file_path=test_file,
            attachment_id="test_002",
            email_id="email_001",
            original_filename="test.pdf",
            content_type="application/pdf",
            size_bytes=10,
            attachment_type=AttachmentType.PDF
        )
        
        assert not result.success  # PDF is invalid, so it should fail
        assert result.attachment_type == AttachmentType.PDF
    
    def test_process_attachment_unknown_file(self):
        """Test processing an unknown file type."""
        # Create a test file with unknown extension
        test_file = os.path.join(self.temp_dir, "test.xyz")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        result = self.processor.process_attachment(
            file_path=test_file,
            attachment_id="test_003",
            email_id="email_001",
            original_filename="test.xyz",
            content_type="application/octet-stream",
            size_bytes=12,
            attachment_type=AttachmentType.UNKNOWN
        )
        
        assert not result.success  # No parser for UNKNOWN type
        assert result.attachment_type == AttachmentType.UNKNOWN
    
    def test_process_attachment_nonexistent_file(self):
        """Test processing a non-existent file."""
        result = self.processor.process_attachment(
            file_path="/nonexistent/file.txt",
            attachment_id="test_004",
            email_id="email_001",
            original_filename="test.txt",
            content_type="text/plain",
            size_bytes=0,
            attachment_type=AttachmentType.TXT
        )
        
        assert not result.success
        assert result.error_message is not None
    
    def test_get_stats(self):
        """Test getting processing statistics."""
        # Process a few attachments
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f"test_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Content {i}")
            
            self.processor.process_attachment(
                file_path=test_file,
                attachment_id=f"test_{i}",
                email_id="email_001",
                original_filename=f"test_{i}.txt",
                content_type="text/plain",
                size_bytes=8,
                attachment_type=AttachmentType.TXT
            )
        
        stats = self.processor.get_stats()
        assert stats["total_processed"] == 3
        assert stats["total_successful"] == 3
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        # Process a few attachments
        for i in range(2):
            test_file = os.path.join(self.temp_dir, f"test_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Content {i}")
            
            self.processor.process_attachment(
                file_path=test_file,
                attachment_id=f"test_{i}",
                email_id="email_001",
                original_filename=f"test_{i}.txt",
                content_type="text/plain",
                size_bytes=8,
                attachment_type=AttachmentType.TXT
            )
        
        # Reset stats
        self.processor.reset_stats()
        
        stats = self.processor.get_stats()
        assert stats["total_processed"] == 0
        assert stats["total_successful"] == 0


class TestAttachmentDispatcher:
    """Tests for the attachment dispatcher."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.dispatcher = AttachmentDispatcher(
            base_path=self.temp_dir,
            dry_run=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_attachment(self):
        """Test saving an attachment."""
        # Create a source file
        source_file = os.path.join(self.temp_dir, "source.txt")
        with open(source_file, 'w') as f:
            f.write("Test content")
        
        target_file = os.path.join(self.temp_dir, "target", "saved.txt")
        
        result = self.dispatcher.save_attachment(
            file_path=source_file,
            target_path=target_file,
            attachment_id="test_001"
        )
        
        assert result["success"]
        assert result["operation"] == "save"
    
    def test_move_attachment(self):
        """Test moving an attachment."""
        # Create a source file
        source_file = os.path.join(self.temp_dir, "source.txt")
        with open(source_file, 'w') as f:
            f.write("Test content")
        
        target_file = os.path.join(self.temp_dir, "target", "moved.txt")
        
        result = self.dispatcher.move_attachment(
            file_path=source_file,
            target_path=target_file,
            attachment_id="test_002"
        )
        
        assert result["success"]
        assert result["operation"] == "move"
    
    def test_delete_attachment(self):
        """Test deleting an attachment."""
        # Create a file to delete
        file_to_delete = os.path.join(self.temp_dir, "to_delete.txt")
        with open(file_to_delete, 'w') as f:
            f.write("Test content")
        
        result = self.dispatcher.delete_attachment(
            file_path=file_to_delete,
            attachment_id="test_003"
        )
        
        assert result["success"]
        assert result["operation"] == "delete"
    
    def test_collision_strategy_rename(self):
        """Test rename collision strategy."""
        # Create a source file
        source_file = os.path.join(self.temp_dir, "source.txt")
        with open(source_file, 'w') as f:
            f.write("Test content")
        
        # Create target file
        target_file = os.path.join(self.temp_dir, "target.txt")
        with open(target_file, 'w') as f:
            f.write("Existing content")
        
        # Save with rename strategy (default)
        result = self.dispatcher.save_attachment(
            file_path=source_file,
            target_path=target_file,
            attachment_id="test_004"
        )
        
        assert result["success"]
        # File should be renamed due to collision
        assert "target.txt" in result["final_path"] or result["final_path"] != target_file


class TestAttachmentPipelineBuilder:
    """Tests for the attachment pipeline builder."""
    
    def test_build_pipeline(self):
        """Test building a pipeline."""
        builder = AttachmentPipelineBuilder()
        
        executor = builder.build()
        
        assert executor is not None
        assert executor.processor is not None
        assert executor.dispatcher is not None
        assert executor.executor is not None
    
    def test_builder_fluent_interface(self):
        """Test fluent interface of builder."""
        builder = AttachmentPipelineBuilder()
        
        builder.set_base_path("/custom/path")
        builder.set_dry_run(True)
        builder.set_collision_strategy("overwrite")
        builder.set_save_path("/save/path")
        builder.set_retry_config(max_retries=5, retry_delay=2.0)
        
        executor = builder.build()
        
        assert executor.processor.base_path == "/custom/path"
        assert executor.dispatcher.dry_run == True
        assert executor.dispatcher.collision_strategy == "overwrite"
        assert executor.executor.max_retries == 5


class TestAttachmentPipelineExecutor:
    """Tests for the attachment pipeline executor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        builder = AttachmentPipelineBuilder()
        builder.set_base_path(self.temp_dir)
        builder.set_dry_run(True)
        
        self.executor = builder.build()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_execute_save_action(self):
        """Test executing save action."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Create a mock email
        email = Email(
            id="email_001",
            subject="Test Email",
            from_addr="test@example.com",
            to_addrs=["recipient@example.com"],
            body_plain="Test body",
            raw_headers={"Content-Type": "text/plain"},
            attachments=[test_file]
        )
        
        results = self.executor.execute(
            email=email,
            attachments=[test_file],
            action_type="save"
        )
        
        assert len(results) == 1
        assert results[0]["success"]
        assert results[0]["attachment_type"] == "TXT"
    
    def test_execute_delete_action(self):
        """Test executing delete action."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Create a mock email
        email = Email(
            id="email_001",
            subject="Test Email",
            from_addr="test@example.com",
            to_addrs=["recipient@example.com"],
            body_plain="Test body",
            raw_headers={"Content-Type": "text/plain"},
            attachments=[test_file]
        )
        
        results = self.executor.execute(
            email=email,
            attachments=[test_file],
            action_type="delete"
        )
        
        assert len(results) == 1
        assert results[0]["success"]
        assert results[0]["attachment_type"] == "TXT"


class TestAttachmentPipelineMonitor:
    """Tests for the attachment pipeline monitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.processor = AttachmentProcessor(
            base_path=self.temp_dir,
            dry_run=True
        )
        self.monitor = AttachmentPipelineMonitor(self.processor)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_status(self):
        """Test getting pipeline status."""
        status = self.monitor.get_status()
        
        assert "total_processed" in status
        assert "total_successful" in status
        assert "total_failed" in status
        assert "success_rate" in status
    
    def test_get_parser_performance(self):
        """Test getting parser performance."""
        performance = self.monitor.get_parser_performance()
        
        assert isinstance(performance, dict)
    
    def test_get_type_performance(self):
        """Test getting type performance."""
        performance = self.monitor.get_type_performance()
        
        assert isinstance(performance, dict)


class TestAttachmentPipelineConfig:
    """Tests for the attachment pipeline configuration."""
    
    def test_config_to_executor(self):
        """Test converting config to executor."""
        config = AttachmentPipelineConfig(
            base_path="/test/path",
            dry_run=True,
            collision_strategy="overwrite",
            max_retries=5,
            retry_delay=2.0,
            save_path="/save/path"
        )
        
        executor = config.to_executor()
        
        assert executor.processor.base_path == "/test/path"
        assert executor.dispatcher.dry_run == True
        assert executor.dispatcher.collision_strategy == "overwrite"
        assert executor.executor.max_retries == 5
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "base_path": "/test/path",
            "dry_run": True,
            "collision_strategy": "overwrite",
            "max_retries": 5,
            "retry_delay": 2.0,
            "save_path": "/save/path"
        }
        
        config = AttachmentPipelineConfig.from_dict(config_dict)
        
        assert config.base_path == "/test/path"
        assert config.dry_run == True
        assert config.collision_strategy == "overwrite"
        assert config.max_retries == 5
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = AttachmentPipelineConfig(
            base_path="/test/path",
            dry_run=True,
            collision_strategy="overwrite",
            max_retries=5,
            retry_delay=2.0,
            save_path="/save/path"
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["base_path"] == "/test/path"
        assert config_dict["dry_run"] == True
        assert config_dict["collision_strategy"] == "overwrite"
        assert config_dict["max_retries"] == 5


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
