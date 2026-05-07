"""
YouTube Studio - Usage Examples

This module provides examples demonstrating how to use the YouTube Studio
components for generating video metadata, transcripts, and templates.
"""

from title_generator import TitleGenerator
from thumbnail_generator import ThumbnailGenerator, ThumbnailStyle
from keyword_generator import KeywordGenerator, KeywordPriority
from transcript_builder import TranscriptBuilder, TranscriptFormat
from studio_orchestrator import StudioOrchestrator


def example_title_generator():
    """Example: Using TitleGenerator"""
    print("=" * 60)
    print("EXAMPLE: Title Generator")
    print("=" * 60)
    
    generator = TitleGenerator(max_length=80)
    
    # Example content
    content = "How to create a YouTube video that gets millions of views"
    
    # Generate a single title
    print("\nGenerating a single title:")
    result = generator.generate_single_title(content)
    print(f"Title: {result.title}")
    print(f"Score: {result.score:.2f}")
    print(f"Style: {result.style}")
    print(f"Description: {result.description}")
    
    # Generate multiple titles
    print("\nGenerating multiple titles:")
    results = generator.generate_titles(content, num_titles=5)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title} (Score: {result.score:.2f})")
    
    print()


def example_thumbnail_generator():
    """Example: Using ThumbnailGenerator"""
    print("=" * 60)
    print("EXAMPLE: Thumbnail Generator")
    print("=" * 60)
    
    generator = ThumbnailGenerator()
    
    # Example content
    content = "Learn Python programming in 30 minutes - Complete tutorial"
    
    # Generate thumbnail suggestions
    print("\nGenerating thumbnail suggestions:")
    thumbnails = generator.generate_thumbnails(content, num_thumbnails=3)
    
    for i, thumbnail in enumerate(thumbnails, 1):
        print(f"\nThumbnail {i}:")
        print(f"  Style: {thumbnail.style}")
        print(f"  Text: {thumbnail.text}")
        print(f"  Description: {thumbnail.description}")
        print(f"  Color Scheme: {thumbnail.color_scheme}")
    
    print()


def example_keyword_generator():
    """Example: Using KeywordGenerator"""
    print("=" * 60)
    print("EXAMPLE: Keyword Generator")
    print("=" * 60)
    
    generator = KeywordGenerator(min_keywords=5, max_keywords=50)
    
    # Example content
    content = "Machine learning tutorial with Python - Complete guide for beginners"
    
    # Generate keywords
    print("\nGenerating keywords:")
    keywords = generator.generate_keywords(content, num_keywords=10)
    
    for i, keyword in enumerate(keywords, 1):
        print(f"{i}. {keyword.keyword} (Priority: {keyword.priority.value}, Relevance: {keyword.relevance_score:.2f})")
    
    print()


def example_transcript_builder():
    """Example: Using TranscriptBuilder"""
    print("=" * 60)
    print("EXAMPLE: Transcript Builder")
    print("=" * 60)
    
    builder = TranscriptBuilder(title="Python Tutorial - Complete Guide")
    
    # Add sections
    builder.add_section(
        title="Introduction",
        content="Welcome to this Python tutorial. In this video, we'll cover the basics of Python programming.",
        start_time=0.0,
        end_time=30.0
    )
    
    builder.add_section(
        title="Python Basics",
        content="Python is a high-level programming language. It's easy to learn and very versatile.",
        start_time=30.0,
        end_time=60.0
    )
    
    builder.add_section(
        title="Variables and Data Types",
        content="Variables store data. Python has several data types including strings, integers, and lists.",
        start_time=60.0,
        end_time=120.0
    )
    
    # Get summary
    summary = builder.get_summary()
    print("\nTranscript Summary:")
    print(f"  Total Sections: {summary['total_sections']}")
    print(f"  Total Words: {summary['total_words']}")
    print(f"  Total Characters: {summary['total_characters']}")
    print(f"  Total Duration: {summary['total_duration']:.1f} seconds")
    
    # Export to SRT
    print("\nExporting to SRT format...")
    builder.export_to_srt("example_transcript.srt")
    print("  Created: example_transcript.srt")
    
    # Export to VTT
    print("\nExporting to VTT format...")
    builder.export_to_vtt("example_transcript.vtt")
    print("  Created: example_transcript.vtt")
    
    print()


def example_studio_orchestrator():
    """Example: Using StudioOrchestrator"""
    print("=" * 60)
    print("EXAMPLE: Studio Orchestrator")
    print("=" * 60)
    
    orchestrator = StudioOrchestrator()
    
    # Example content
    content = """Complete guide to building a YouTube automation channel.
    
In this comprehensive tutorial, we'll cover everything from setting up your channel
to creating engaging content that gets millions of views.
    
We'll discuss content strategy, video optimization, thumbnail design, and audience
engagement techniques. Perfect for beginners who want to start their YouTube journey."""
    
    # Process content
    print("\nProcessing content...")
    result = orchestrator.process_content(
        content=content,
        video_category="Education",
        target_audience="Beginners and intermediate creators"
    )
    
    if result.success:
        print("\nGenerated Video Metadata:")
        print(f"  Title: {result.metadata.title}")
        print(f"  Description: {result.metadata.description[:100]}...")
        print(f"  Keywords: {', '.join(result.metadata.keywords[:5])}")
        print(f"  Tags: {', '.join(result.metadata.tags[:5])}")
        print(f"  Category: {result.metadata.category}")
        print(f"  Target Audience: {result.metadata.target_audience}")
        
        print("\n  Thumbnail Suggestions:")
        for i, thumbnail in enumerate(result.metadata.thumbnail_suggestions[:2], 1):
            print(f"    {i}. Style: {thumbnail.style}")
            print(f"       Text: {thumbnail.text}")
            print(f"       Description: {thumbnail.description}")
        
        # Validate metadata
        print("\nValidating metadata...")
        is_valid, issues = orchestrator.validate_metadata(result.metadata)
        
        if is_valid:
            print("  ✓ Metadata is valid!")
        else:
            print("  ⚠ Metadata has issues:")
            for issue in issues:
                print(f"    - {issue}")
        
        # Export metadata
        print("\nExporting metadata to JSON...")
        output_path = orchestrator.export_metadata(
            result.metadata,
            format='json',
            output_path='example_metadata.json'
        )
        print(f"  Created: {output_path}")
        
    else:
        print(f"\nError: {result.errors}")
    
    print()


def example_complete_workflow():
    """Example: Complete workflow with transcript and metadata"""
    print("=" * 60)
    print("EXAMPLE: Complete Workflow")
    print("=" * 60)
    
    orchestrator = StudioOrchestrator()
    
    # Step 1: Process transcript
    print("\nStep 1: Processing transcript...")
    transcript_content = """
    Introduction
    Welcome to this tutorial on building a YouTube channel.
    
    Content Strategy
    Planning your content is crucial for success.
    
    Video Creation
    Focus on quality and consistency.
    
    Optimization
    Use good titles, descriptions, and thumbnails.
    
    Conclusion
    Thanks for watching!
    """
    
    transcript_result = orchestrator.process_transcript(
        content=transcript_content,
        title="YouTube Channel Building Guide"
    )
    
    print(f"  Title: {transcript_result.transcript.title}")
    print(f"  Sections: {len(transcript_result.transcript.sections)}")
    print(f"  Duration: {transcript_result.transcript.total_duration:.1f}s")
    print(f"  Word Count: {transcript_result.transcript.word_count}")
    
    # Step 2: Generate metadata from transcript
    print("\nStep 2: Generating metadata...")
    metadata_result = orchestrator.process_content(
        content=transcript_content,
        video_category="Education",
        target_audience="Content creators"
    )
    
    print(f"  Title: {metadata_result.metadata.title}")
    print(f"  Keywords: {len(metadata_result.metadata.keywords)}")
    
    # Step 3: Export everything
    print("\nStep 3: Exporting...")
    
    # Export transcript
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save transcript as SRT
    srt_path = f"transcript_{timestamp}.srt"
    orchestrator._transcript_builder = TranscriptBuilder(title=transcript_result.transcript.title)
    for section in transcript_result.transcript.sections:
        orchestrator._transcript_builder.add_section(
            title=section.title,
            content=section.content,
            start_time=section.start_time,
            end_time=section.end_time
        )
    orchestrator._transcript_builder.export_to_srt(srt_path)
    print(f"  Created: {srt_path}")
    
    # Export metadata
    json_path = orchestrator.export_metadata(
        metadata_result.metadata,
        format='json',
        output_path=f"metadata_{timestamp}.json"
    )
    print(f"  Created: {json_path}")
    
    print("\n✓ Complete workflow finished!")
    print()


def example_template_usage():
    """Example: Using templates"""
    print("=" * 60)
    print("EXAMPLE: Template Usage")
    print("=" * 60)
    
    orchestrator = StudioOrchestrator()
    
    # Create a custom template
    template_name = "custom_video_template"
    template_data = {
        'variables': ['video_title', 'main_topic', 'keywords'],
        'content': {
            'title_template': '{{video_title}} - {{main_topic}}',
            'description_template': '{{video_title}}\n\nKeywords: {{keywords}}',
            'thumbnail_text': '{{main_topic}}'
        }
    }
    
    orchestrator.template_manager.save_template(
        name=template_name,
        content=template_data,
        description="Custom video metadata template",
        version="1.0.0",
        tags=["custom", "video"]
    )
    
    print(f"\nSaved template: {template_name}")
    
    # Use the template
    print("\nGenerating metadata using template...")
    result = orchestrator.generate_from_template(
        template_name=template_name,
        variables={
            'video_title': 'Complete Python Tutorial',
            'main_topic': 'Python Programming',
            'keywords': 'Python, Programming, Tutorial, Beginner'
        }
    )
    
    print(f"  Template: {result['template_name']}")
    print(f"  Rendered Title: {result['rendered'].split('\n')[0]}")
    print(f"  Variables Used: {', '.join(result['variables_used'])}")
    
    print()


def run_all_examples():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("YOUTUBE STUDIO - USAGE EXAMPLES")
    print("=" * 60 + "\n")
    
    example_title_generator()
    example_thumbnail_generator()
    example_keyword_generator()
    example_transcript_builder()
    example_studio_orchestrator()
    example_complete_workflow()
    example_template_usage()
    
    print("=" * 60)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    run_all_examples()
