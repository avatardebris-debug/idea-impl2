"""
Example script demonstrating the attachment processing module.

This script shows how to:
1. Process email attachments
2. Parse different attachment types (PDF, Office documents, text files)
3. Execute actions (save, move, delete)
4. Monitor processing progress
5. Use the pipeline builder for custom configurations
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the workspace directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'workspace'))

from email_tool.attachment_types import (
    AttachmentType,
    get_attachment_type,
    is_text_attachment,
    is_pdf_attachment,
    is_office_attachment
)
from email_tool.attachment_processor import (
    AttachmentProcessor,
    AttachmentDispatcher,
    AttachmentActionExecutor,
    AttachmentPipelineBuilder,
    AttachmentPipelineExecutor,
    AttachmentPipelineMonitor,
    AttachmentPipelineConfig
)
from email_tool.models import Email


def example_1_basic_processing():
    """Example 1: Basic attachment processing."""
    print("\n" + "="*60)
    print("Example 1: Basic Attachment Processing")
    print("="*60)
    
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize the processor
        processor = AttachmentProcessor(
            base_path=temp_dir,
            dry_run=True
        )
        
        # Create a test text file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("This is a test file content.")
        
        # Process the attachment
        result = processor.process_attachment(
            file_path=test_file,
            attachment_id="test_001",
            email_id="email_001",
            original_filename="test.txt",
            content_type="text/plain",
            size_bytes=30,
            attachment_type=AttachmentType.TXT
        )
        
        print(f"Attachment ID: {result.attachment_id}")
        print(f"Original filename: {result.original_filename}")
        print(f"Attachment type: {result.attachment_type.name}")
        print(f"Success: {result.success}")
        print(f"Text content: {result.text_content}")
        
        # Get statistics
        stats = processor.get_stats()
        print(f"\nProcessing Statistics:")
        print(f"  Total processed: {stats['total_processed']}")
        print(f"  Successful: {stats['total_successful']}")
        print(f"  Failed: {stats['total_failed']}")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_2_dispatcher_actions():
    """Example 2: Dispatcher actions (save, move, delete)."""
    print("\n" + "="*60)
    print("Example 2: Dispatcher Actions")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize the dispatcher
        dispatcher = AttachmentDispatcher(
            base_path=temp_dir,
            dry_run=True
        )
        
        # Create a source file
        source_file = os.path.join(temp_dir, "source.txt")
        with open(source_file, 'w') as f:
            f.write("Source content")
        
        # Save action
        print("\n1. Save Action:")
        target_file = os.path.join(temp_dir, "saved.txt")
        result = dispatcher.save_attachment(
            file_path=source_file,
            target_path=target_file,
            attachment_id="save_001"
        )
        print(f"   Success: {result['success']}")
        print(f"   Final path: {result.get('final_path', 'N/A')}")
        
        # Move action
        print("\n2. Move Action:")
        target_file = os.path.join(temp_dir, "moved.txt")
        result = dispatcher.move_attachment(
            file_path=source_file,
            target_path=target_file,
            attachment_id="move_001"
        )
        print(f"   Success: {result['success']}")
        print(f"   Final path: {result.get('final_path', 'N/A')}")
        
        # Delete action
        print("\n3. Delete Action:")
        file_to_delete = os.path.join(temp_dir, "delete_me.txt")
        with open(file_to_delete, 'w') as f:
            f.write("To be deleted")
        
        result = dispatcher.delete_attachment(
            file_path=file_to_delete,
            attachment_id="delete_001"
        )
        print(f"   Success: {result['success']}")
        
        # Get operation log
        operations = dispatcher.get_operations_log()
        print(f"\nTotal operations: {len(operations)}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_3_pipeline_builder():
    """Example 3: Using the pipeline builder."""
    print("\n" + "="*60)
    print("Example 3: Pipeline Builder")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Build a custom pipeline
        builder = AttachmentPipelineBuilder()
        
        builder.set_base_path(temp_dir)
        builder.set_dry_run(True)
        builder.set_collision_strategy("rename")
        builder.set_save_path(os.path.join(temp_dir, "processed"))
        builder.set_retry_config(max_retries=5, retry_delay=1.0)
        
        # Build the executor
        executor = builder.build()
        
        print(f"Base path: {executor.processor.base_path}")
        print(f"Dry run: {executor.processor.dry_run}")
        print(f"Collision strategy: {executor.dispatcher.collision_strategy}")
        print(f"Max retries: {executor.executor.max_retries}")
        
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("Test content for pipeline")
        
        # Create a mock email
        email = Email(
            id="email_001",
            subject="Test Email",
            sender="test@example.com",
            recipients=["recipient@example.com"],
            body="Test body",
            raw_headers={"Content-Type": "text/plain"},
            attachments=[test_file]
        )
        
        # Execute the pipeline
        print("\nExecuting pipeline...")
        results = executor.execute(
            email=email,
            attachments=[test_file],
            action_type="save"
        )
        
        print(f"Results: {len(results)} attachments processed")
        for result in results:
            print(f"  - {result['original_filename']}: {result['message']}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_4_pipeline_monitor():
    """Example 4: Monitoring pipeline progress."""
    print("\n" + "="*60)
    print("Example 4: Pipeline Monitoring")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize processor and monitor
        processor = AttachmentProcessor(
            base_path=temp_dir,
            dry_run=True
        )
        
        monitor = AttachmentPipelineMonitor(processor)
        
        # Process several attachments
        for i in range(5):
            test_file = os.path.join(temp_dir, f"test_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"Content {i}")
            
            processor.process_attachment(
                file_path=test_file,
                attachment_id=f"test_{i}",
                email_id="email_001",
                original_filename=f"test_{i}.txt",
                content_type="text/plain",
                size_bytes=8,
                attachment_type=AttachmentType.TXT
            )
        
        # Get status
        status = monitor.get_status()
        print(f"\nPipeline Status:")
        print(f"  Total processed: {status['total_processed']}")
        print(f"  Successful: {status['total_successful']}")
        print(f"  Failed: {status['total_failed']}")
        print(f"  Success rate: {status['success_rate']:.1f}%")
        
        # Get parser performance
        parser_perf = monitor.get_parser_performance()
        print(f"\nParser Performance:")
        for parser, perf in parser_perf.items():
            print(f"  {parser}: {perf['processed']} processed ({perf['percentage']:.1f}%)")
        
        # Get type performance
        type_perf = monitor.get_type_performance()
        print(f"\nAttachment Type Performance:")
        for att_type, perf in type_perf.items():
            print(f"  {att_type}: {perf['processed']} processed ({perf['percentage']:.1f}%)")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_5_config_management():
    """Example 5: Configuration management."""
    print("\n" + "="*60)
    print("Example 5: Configuration Management")
    print("="*60)
    
    # Create a configuration
    config = AttachmentPipelineConfig(
        base_path="/custom/path",
        dry_run=True,
        collision_strategy="overwrite",
        max_retries=5,
        retry_delay=2.0,
        save_path="/save/path"
    )
    
    print(f"Configuration:")
    print(f"  Base path: {config.base_path}")
    print(f"  Dry run: {config.dry_run}")
    print(f"  Collision strategy: {config.collision_strategy}")
    print(f"  Max retries: {config.max_retries}")
    print(f"  Retry delay: {config.retry_delay}s")
    print(f"  Save path: {config.save_path}")
    
    # Convert to dictionary
    config_dict = config.to_dict()
    print(f"\nConfiguration as dictionary:")
    for key, value in config_dict.items():
        print(f"  {key}: {value}")
    
    # Create from dictionary
    config_dict2 = {
        "base_path": "/new/path",
        "dry_run": False,
        "collision_strategy": "rename",
        "max_retries": 3,
        "retry_delay": 1.5,
        "save_path": "/new/save/path"
    }
    
    config2 = AttachmentPipelineConfig.from_dict(config_dict2)
    print(f"\nConfiguration from dictionary:")
    print(f"  Base path: {config2.base_path}")
    print(f"  Dry run: {config2.dry_run}")
    
    # Convert config to executor
    executor = config2.to_executor()
    print(f"\nExecutor from config:")
    print(f"  Base path: {executor.processor.base_path}")
    print(f"  Dry run: {executor.processor.dry_run}")


def example_6_attachment_type_detection():
    """Example 6: Attachment type detection."""
    print("\n" + "="*60)
    print("Example 6: Attachment Type Detection")
    print("="*60)
    
    # Test various file types
    test_cases = [
        ("document.pdf", "application/pdf"),
        ("report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("presentation.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
        ("notes.txt", "text/plain"),
        ("data.csv", "text/csv"),
        ("image.jpg", "image/jpeg"),
        ("photo.png", "image/png"),
        ("unknown.xyz", "application/octet-stream"),
    ]
    
    print("\nAttachment Type Detection:")
    for filename, mime_type in test_cases:
        attachment_type = get_attachment_type(
            mime_type=mime_type,
            filename=filename
        )
        
        print(f"\n  {filename}")
        print(f"    MIME: {mime_type}")
        print(f"    Type: {attachment_type.name}")
        print(f"    Is text: {is_text_attachment(attachment_type)}")
        print(f"    Is image: {is_text_attachment(attachment_type)}")
        print(f"    Is Office: {is_office_attachment(attachment_type)}")
        print(f"    Is PDF: {is_pdf_attachment(attachment_type)}")
    
    # Get supported types
    supported = AttachmentProcessor.get_supported_types()
    print(f"\nSupported attachment types: {len(supported)}")
    for att_type in supported:
        print(f"  - {att_type.name}")


def example_7_error_handling():
    """Example 7: Error handling and retry logic."""
    print("\n" + "="*60)
    print("Example 7: Error Handling and Retry Logic")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize processor with retry config
        processor = AttachmentProcessor(
            base_path=temp_dir,
            dry_run=True
        )
        
        # Try to process a non-existent file
        print("\n1. Processing non-existent file:")
        result = processor.process_attachment(
            file_path="/nonexistent/file.txt",
            attachment_id="error_001",
            email_id="email_001",
            original_filename="file.txt",
            content_type="text/plain",
            size_bytes=0,
            attachment_type=AttachmentType.TXT
        )
        
        print(f"   Success: {result.success}")
        print(f"   Error: {result.error_message}")
        
        # Get statistics
        stats = processor.get_stats()
        print(f"\n2. Statistics after error:")
        print(f"   Total processed: {stats['total_processed']}")
        print(f"   Successful: {stats['total_successful']}")
        print(f"   Failed: {stats['total_failed']}")
        
        # Reset statistics
        processor.reset_stats()
        stats = processor.get_stats()
        print(f"\n3. Statistics after reset:")
        print(f"   Total processed: {stats['total_processed']}")
        print(f"   Successful: {stats['total_successful']}")
        print(f"   Failed: {stats['total_failed']}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def example_8_real_world_scenario():
    """Example 8: Real-world scenario - Email attachment processing."""
    print("\n" + "="*60)
    print("Example 8: Real-World Scenario")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Build a pipeline for real-world usage
        builder = AttachmentPipelineBuilder()
        builder.set_base_path(temp_dir)
        builder.set_dry_run(False)  # In real usage, set to False
        builder.set_collision_strategy("rename")
        builder.set_save_path(os.path.join(temp_dir, "processed_attachments"))
        builder.set_retry_config(max_retries=3, retry_delay=1.0)
        
        executor = builder.build()
        
        # Simulate an email with multiple attachments
        email = Email(
            id="email_001",
            subject="Project Documents",
            sender="colleague@example.com",
            recipients=["me@example.com"],
            body="Please find attached the project documents.",
            raw_headers={"Content-Type": "text/plain"},
            attachments=[]
        )
        
        # Create various attachment files
        attachments = []
        
        # PDF document
        pdf_file = os.path.join(temp_dir, "project_spec.pdf")
        with open(pdf_file, 'wb') as f:
            f.write(b"%PDF-1.4\n")
        attachments.append(pdf_file)
        
        # Word document
        docx_file = os.path.join(temp_dir, "requirements.docx")
        with open(docx_file, 'wb') as f:
            f.write(b"PK")  # Minimal DOCX signature
        attachments.append(docx_file)
        
        # Text file
        txt_file = os.path.join(temp_dir, "notes.txt")
        with open(txt_file, 'w') as f:
            f.write("Important notes for the project.\n")
        attachments.append(txt_file)
        
        # Process all attachments
        print("\nProcessing email attachments...")
        results = executor.execute(
            email=email,
            attachments=attachments,
            action_type="save"
        )
        
        print(f"\nProcessed {len(results)} attachments:")
        for result in results:
            print(f"  - {result['original_filename']} ({result['attachment_type']})")
            print(f"    Status: {result['message']}")
        
        # Get monitoring information
        monitor = AttachmentPipelineMonitor(executor.processor)
        status = monitor.get_status()
        
        print(f"\nProcessing Summary:")
        print(f"  Total: {status['total_processed']}")
        print(f"  Success: {status['total_successful']}")
        print(f"  Failed: {status['total_failed']}")
        print(f"  Success Rate: {status['success_rate']:.1f}%")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Email Attachment Processing Module - Examples")
    print("="*60)
    
    # Run all examples
    example_1_basic_processing()
    example_2_dispatcher_actions()
    example_3_pipeline_builder()
    example_4_pipeline_monitor()
    example_5_config_management()
    example_6_attachment_type_detection()
    example_7_error_handling()
    example_8_real_world_scenario()
    
    print("\n" + "="*60)
    print("All examples completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
