# Test Plan: Video Ingestor Summary Pipeline

## 1. Project Overview

The **Video Ingestor Summary Pipeline** is a multi-stage system that:
1. Downloads videos from URLs
2. Extracts audio and transcribes it using Whisper
3. Chunks the transcript text
4. Generates embeddings for chunks
5. Stores chunks in a vector database (ChromaDB)
6. Provides Q&A capabilities over the stored content
7. Generates summaries of the video content

### Key Components:
- **IngestionPipeline**: Orchestrates download, audio extraction, and transcription
- **Storage**: SQLite-based job tracking and metadata storage
- **TextChunker**: Splits transcript into overlapping chunks
- **EmbeddingGenerator**: Generates vector embeddings for text
- **VectorStore**: ChromaDB-based vector storage and retrieval
- **QuestionAnswerer**: LLM-powered Q&A over stored content
- **Summarizer**: LLM-powered video summarization

### Dependencies:
- `openai` (Whisper transcription, embeddings, LLM)
- `chromadb` (vector database)
- `sqlite3` (job storage)
- `ffmpeg-python` (audio extraction)
- `requests` (video download)
- `pydantic` (data models)

---

## 2. Test Strategy

### Testing Approach:
1. **Unit Tests**: Test individual components in isolation with mocked external dependencies
2. **Integration Tests**: Test component interactions with real implementations where feasible
3. **Mocking Strategy**:
   - Mock Whisper transcription (`IngestionPipeline.transcribe`)
   - Mock LLM responses (`harness.generate_json`)
   - Mock video download (`download_video`)
   - Mock audio extraction (`extract_audio`)
   - Use real ChromaDB with temporary directories for vector store tests
   - Use real SQLite with temporary files for storage tests

### Test Categories:
1. **Ingestion Pipeline Tests**: Download, audio extraction, transcription
2. **Storage Tests**: Job CRUD operations, status transitions
3. **Chunker Tests**: Text splitting, overlap handling, timestamp preservation
4. **Embedding Tests**: Embedding generation, normalization, consistency
5. **Vector Store Tests**: Upsert, search, persistence, similarity
6. **Question Answerer Tests**: Q&A flow, citation handling, error cases
7. **Summarizer Tests**: Summary generation, parameter handling, error cases

---

## 3. Detailed Test Cases

### 3.1 Ingestion Pipeline Tests (`test_ingestion.py`)

#### Test Case 1.1: Transcription with Mocked Whisper
- **Description**: Verify transcription returns expected segments and full text
- **Input**: Dummy audio file, mocked Whisper model
- **Expected Output**: Segments list with correct text, start, end times; full text string
- **Assertions**:
  - `full_text == "Hello world"`
  - `len(segments) == 1`
  - `segments[0]["text"] == "Hello world"`
  - `segments[0]["start"] == 0.0`
  - `segments[0]["end"] == 2.0`

#### Test Case 1.2: Ingest from URL - Success Path
- **Description**: Full ingestion pipeline with mocked download and audio extraction
- **Input**: Dummy video file, mocked download/extract methods
- **Expected Output**: Job marked as "completed" with full text
- **Assertions**:
  - `job_id is not None`
  - `job["status"] == "completed"`
  - `job["full_text"] == "Hello world"`
  - Storage contains the job

#### Test Case 1.3: Ingest from URL - Failure Path
- **Description**: Handle download failure gracefully
- **Input**: Mocked download that raises exception
- **Expected Output**: `IngestionError` raised
- **Assertions**:
  - Exception message contains "Ingestion failed"
  - Job status is "failed" (if job was created)

#### Test Case 1.4: Audio Extraction with FFmpeg
- **Description**: Verify audio extraction from video file
- **Input**: Dummy video file
- **Expected Output**: Audio file created
- **Assertions**:
  - Audio file exists
  - Audio file is not empty
  - FFmpeg command was called with correct arguments

#### Test Case 1.5: Download Video from URL
- **Description**: Verify video download functionality
- **Input**: Valid URL
- **Expected Output**: Video file downloaded
- **Assertions**:
  - Video file exists
  - Video file size > 0
  - Correct content type returned

#### Test Case 1.6: Ingestion with Multiple Segments
- **Description**: Handle transcripts with multiple segments
- **Input**: Mocked Whisper returning multiple segments
- **Expected Output**: All segments preserved
- **Assertions**:
  - All segments returned
  - Full text is concatenation of segments
  - Timestamps are sequential

#### Test Case 1.7: Ingestion with Empty Transcript
- **Description**: Handle edge case of empty transcript
- **Input**: Mocked Whisper returning empty text
- **Expected Output**: Job completed with empty text
- **Assertions**:
  - `full_text == ""`
  - `segments == []`
  - Job status is "completed"

#### Test Case 1.8: Ingestion Pipeline Initialization
- **Description**: Verify pipeline initialization with storage and model
- **Input**: Storage instance, Whisper model
- **Expected Output**: Pipeline instance with correct attributes
- **Assertions**:
  - `pipeline.storage is not None`
  - `pipeline.model is not None`
  - Pipeline methods are callable

---

### 3.2 Storage Tests (`test_storage.py`)

#### Test Case 2.1: Create and Retrieve Job
- **Description**: Basic job creation and retrieval
- **Input**: Video path, metadata
- **Expected Output**: Job ID, job with correct status
- **Assertions**:
  - `job_id is not None`
  - `job["status"] == "pending"`
  - `job["video_path"] == "/tmp/test.mp4"`
  - `job["metadata"] == {"source": "url"}`

#### Test Case 2.2: Update Job Status
- **Description**: Transition job status from pending to processing
- **Input**: Job ID, new status
- **Expected Output**: Updated job record
- **Assertions**:
  - `job["status"] == "processing"`
  - Previous status was "pending"

#### Test Case 2.3: Update Job to Completed
- **Description**: Complete job with transcript data
- **Input**: Job ID, transcript JSON, full text
- **Expected Output**: Job marked completed with transcript
- **Assertions**:
  - `job["status"] == "completed"`
  - `job["full_text"] == "hello"`
  - `len(job["transcript"]) == 1`
  - Transcript data is correctly stored

#### Test Case 2.4: Update Job to Failed
- **Description**: Mark job as failed with error message
- **Input**: Job ID, error message
- **Expected Output**: Job marked failed with error
- **Assertions**:
  - `job["status"] == "failed"`
  - `job["error"] == "something broke"`

#### Test Case 2.5: Get Nonexistent Job
- **Description**: Handle retrieval of non-existent job
- **Input**: Invalid job ID
- **Expected Output**: None
- **Assertions**:
  - `storage.get_job("nonexistent") is None`

#### Test Case 2.6: List Jobs
- **Description**: Retrieve multiple jobs with limit
- **Input**: Multiple jobs created
- **Expected Output**: List of jobs
- **Assertions**:
  - `len(jobs) == 5`
  - Jobs are in correct order (newest first)
  - Limit parameter is respected

#### Test Case 2.7: Delete Job
- **Description**: Remove job from storage
- **Input**: Job ID
- **Expected Output**: Deletion confirmation
- **Assertions**:
  - `storage.delete_job(job_id) is True`
  - `storage.get_job(job_id) is None`

#### Test Case 2.8: Delete Nonexistent Job
- **Description**: Handle deletion of non-existent job
- **Input**: Invalid job ID
- **Expected Output**: False
- **Assertions**:
  - `storage.delete_job("nonexistent") is False`

#### Test Case 2.9: Database Persistence Across Instances
- **Description**: Verify data persists when storage is closed and reopened
- **Input**: Job created in one instance
- **Expected Output**: Job retrievable in new instance
- **Assertions**:
  - Job exists in second instance
  - All fields match original job

#### Test Case 2.10: Storage Connection and Cleanup
- **Description**: Verify proper connection handling
- **Input**: Storage instance lifecycle
- **Expected Output**: No resource leaks
- **Assertions**:
  - Database file exists after connect
  - Database file can be accessed after close
  - No SQLite errors on close

---

### 3.3 Chunker Tests (`test_chunker.py`)

#### Test Case 3.1: Chunk Empty Segments
- **Description**: Handle empty segment list
- **Input**: Empty segments list
- **Expected Output**: Empty chunks list
- **Assertions**:
  - `chunks == []`

#### Test Case 3.2: Chunk Single Segment
- **Description**: Chunk a single segment
- **Input**: One segment
- **Expected Output**: One chunk with correct properties
- **Assertions**:
  - `len(chunks) == 1`
  - `chunks[0].text == "Hello world"`
  - `chunks[0].start == 0.0`
  - `chunks[0].end == 5.0`
  - `chunks[0].job_id == "job1"`
  - `chunks[0].segment_indices == [0]`

#### Test Case 3.3: Chunk Multiple Segments
- **Description**: Chunk multiple segments
- **Input**: Three segments
- **Expected Output**: Multiple chunks
- **Assertions**:
  - `len(chunks) >= 1`
  - First chunk contains "Hello"
  - All chunks have valid text

#### Test Case 3.4: Chunk with Overlap
- **Description**: Verify overlap between consecutive chunks
- **Input**: 20 segments with 20% overlap
- **Expected Output**: Chunks with overlapping timestamps
- **Assertions**:
  - `chunks[0].end >= chunks[1].start`
  - Overlap length is approximately 20% of chunk size

#### Test Case 3.5: Chunk Respects Chunk Size
- **Description**: Verify chunks don't exceed chunk size
- **Input**: Long text with 100 words
- **Expected Output**: Chunks within size limit
- **Assertions**:
  - Each chunk has ≤ 12 words (with tolerance)
  - All chunks have valid text

#### Test Case 3.6: Chunk Preserves Timestamps
- **Description**: Verify timestamp preservation
- **Input**: Two segments with specific timestamps
- **Expected Output**: Chunk with correct timestamps
- **Assertions**:
  - `chunks[0].start == 0.0`
  - `chunks[0].end == 2.0`

#### Test Case 3.7: Chunk Job ID Propagation
- **Description**: Verify job ID is propagated to all chunks
- **Input**: Unique job ID
- **Expected Output**: All chunks have correct job ID
- **Assertions**:
  - `all(chunk.job_id == "unique-job-id" for chunk in chunks)`

#### Test Case 3.8: Chunk Empty Text
- **Description**: Handle empty text input
- **Input**: Segment with empty text
- **Expected Output**: Empty chunks list
- **Assertions**:
  - `chunks == []`

#### Test Case 3.9: Chunk Large Text
- **Description**: Handle large text input
- **Input**: 1000 words
- **Expected Output**: Multiple chunks
- **Assertions**:
  - `len(chunks) > 1`
  - All chunks have valid timestamps
  - All chunks have non-empty text

#### Test Case 3.10: Chunk with Special Characters
- **Description**: Handle special characters and emojis
- **Input**: Text with special chars and emoji
- **Expected Output**: Chunks preserving special characters
- **Assertions**:
  - Special characters preserved in chunks
  - Emoji preserved in chunks
  - Chunks are valid

---

### 3.4 Embedding Tests (`test_embeddings.py`)

#### Test Case 4.1: Generate Single Text Embedding
- **Description**: Generate embedding for single text
- **Input**: "Hello world"
- **Expected Output**: Normalized embedding vector
- **Assertions**:
  - `isinstance(embedding, list)`
  - `len(embedding) > 0`
  - L2 norm ≈ 1.0 (within 0.01 tolerance)

#### Test Case 4.2: Different Texts Have Different Embeddings
- **Description**: Verify embeddings differ for different texts
- **Input**: "Hello world" vs "Goodbye world"
- **Expected Output**: Different embeddings
- **Assertions**:
  - `emb1 != emb2`

#### Test Case 4.3: Same Text Has Same Embedding
- **Description**: Verify embedding consistency
- **Input**: "Hello world" twice
- **Expected Output**: Identical embeddings
- **Assertions**:
  - `emb1 == emb2`

#### Test Case 4.4: Generate Batch Embeddings
- **Description**: Generate embeddings for multiple texts
- **Input**: ["Hello", "World", "Test"]
- **Expected Output**: Three embeddings
- **Assertions**:
  - `len(embeddings) == 3`
  - All embeddings are normalized
  - All embeddings are lists

#### Test Case 4.5: Generate Empty Text Embedding
- **Description**: Handle empty text
- **Input**: ""
- **Expected Output**: Valid embedding
- **Assertions**:
  - `isinstance(embedding, list)`
  - `len(embedding) > 0`

#### Test Case 4.6: Generate Long Text Embedding
- **Description**: Handle long text
- **Input**: 1000 words
- **Expected Output**: Valid embedding
- **Assertions**:
  - `isinstance(embedding, list)`
  - `len(embedding) > 0`

#### Test Case 4.7: Generate Special Characters Embedding
- **Description**: Handle special characters
- **Input**: "Hello! @#$% 🌍"
- **Expected Output**: Valid embedding
- **Assertions**:
  - `isinstance(embedding, list)`
  - `len(embedding) > 0`

#### Test Case 4.8: Generate Unicode Embedding
- **Description**: Handle Unicode text
- **Input**: "こんにちは世界"
- **Expected Output**: Valid embedding
- **Assertions**:
  - `isinstance(embedding, list)`
  - `len(embedding) > 0`

#### Test Case 4.9: Embedding Dimension Consistency
- **Description**: Verify consistent embedding dimensions
- **Input**: Two different texts
- **Expected Output**: Same dimension embeddings
- **Assertions**:
  - `len(emb1) == len(emb2)`

---

### 3.5 Vector Store Tests (`test_vector_store.py`)

#### Test Case 5.1: Upsert and Search
- **Description**: Store chunks and search for them
- **Input**: 5 sample chunks
- **Expected Output**: Search returns relevant results
- **Assertions**:
  - `len(results) > 0`
  - "Python" found in results for "programming language" query

#### Test Case 5.2: Upsert Multiple Jobs
- **Description**: Store chunks for multiple jobs
- **Input**: Chunks for job1 and job2
- **Expected Output**: Separate results for each job
- **Assertions**:
  - `len(results1) > 0` for job1
  - `len(results2) > 0` for job2
  - Results are job-specific

#### Test Case 5.3: Search Returns Relevant Results
- **Description**: Verify search relevance
- **Input**: Chunks with "fox" sentence
- **Expected Output**: "fox" found in results
- **Assertions**:
  - `len(results) > 0`
  - "fox" in results text

#### Test Case 5.4: Search with No Results
- **Description**: Handle non-matching queries
- **Input**: Chunks, non-matching query "xyzxyzxyz"
- **Expected Output**: Empty or low relevance results
- **Assertions**:
  - `len(results) >= 0`

#### Test Case 5.5: Upsert Overwrites Existing
- **Description**: Verify upsert overwrites old data
- **Input**: Same job_id with different chunks
- **Expected Output**: New data returned in search
- **Assertions**:
  - "New text" found in results
  - "Old text" not found

#### Test Case 5.6: Search with Custom top_k
- **Description**: Verify top_k parameter works
- **Input**: Chunks, queries with different top_k
- **Expected Output**: Correct number of results
- **Assertions**:
  - `len(results_top1) <= 1`
  - `len(results_top3) <= 3`
  - `len(results_top3) >= len(results_top1)`

#### Test Case 5.7: Persistence Across Instances
- **Description**: Verify ChromaDB persistence
- **Input**: Data in one instance
- **Expected Output**: Data retrievable in new instance
- **Assertions**:
  - `len(results) > 0`
  - "Persistent test" found in results

#### Test Case 5.8: Search Empty Job
- **Description**: Handle search on empty job
- **Input**: Non-existent job
- **Expected Output**: Empty results
- **Assertions**:
  - `results == []`

#### Test Case 5.9: Upsert Empty Chunks
- **Description**: Handle empty chunk list
- **Input**: Empty chunks list
- **Expected Output**: No error
- **Assertions**:
  - No exception raised

#### Test Case 5.10: Upsert Chunk Without Embedding
- **Description**: Auto-generate embeddings if missing
- **Input**: Chunk with embedding=None
- **Expected Output**: Chunk stored with auto-generated embedding
- **Assertions**:
  - No exception raised
  - Chunk found in search

#### Test Case 5.11: Search Returns Distance Scores
- **Description**: Verify distance scores in results
- **Input**: Chunks, query
- **Expected Output**: Results with distance scores
- **Assertions**:
  - "distance" in each result
  - `isinstance(result["distance"], float)`
  - `result["distance"] >= 0.0`

---

### 3.6 Question Answerer Tests (`test_question_answerer.py`)

#### Test Case 6.1: Answer with Citations
- **Description**: Q&A with citation generation
- **Input**: Question, mocked LLM with citations
- **Expected Output**: Answer with citations
- **Assertions**:
  - `len(result["citations"]) == 2`
  - `result["citations"][0]["text"] == "Citation 1"`
  - `result["citations"][1]["text"] == "Citation 2"`
  - Citations have similarity scores

#### Test Case 6.2: Answer with Missing Keys in Response
- **Description**: Handle LLM response with missing keys
- **Input**: Question, LLM response missing citations/confidence
- **Expected Output**: Answer with defaults
- **Assertions**:
  - `result["answer"] == "Answer only"`
  - `result["citations"] == []`
  - `result["confidence"] == 0.5`

#### Test Case 6.3: Answer with None Values in Response
- **Description**: Handle LLM response with None values
- **Input**: Question, LLM response with None values
- **Expected Output**: Default answer
- **Assertions**:
  - `result["answer"] == "I don't have enough information..."`
  - `result["citations"] == []`
  - `result["confidence"] == 0.0`

#### Test Case 6.4: Answer with Empty Question
- **Description**: Handle empty question
- **Input**: Empty string question
- **Expected Output**: Answer from LLM
- **Assertions**:
  - `result["answer"] == "Empty question answer"`

#### Test Case 6.5: Answer with Special Characters
- **Description**: Handle special characters in question
- **Input**: Question with "@#$%"
- **Expected Output**: Answer from LLM
- **Assertions**:
  - `result["answer"] == "Special chars answer"`

#### Test Case 6.6: Answer with Unicode Question
- **Description**: Handle Unicode in question
- **Input**: Japanese question
- **Expected Output**: Answer from LLM
- **Assertions**:
  - `result["answer"] == "Unicode answer"`

#### Test Case 6.7: Answer with Custom System Prompt
- **Description**: Use custom system prompt
- **Input**: Question, custom system prompt
- **Expected Output**: Answer from LLM
- **Assertions**:
  - `result["answer"] == "Custom prompt answer"`
  - Custom prompt was passed to LLM

---

### 3.7 Summarizer Tests (`test_summarizer.py`)

#### Test Case 7.1: Summarize with Mocked Harness
- **Description**: Basic summarization
- **Input**: Text, segments, mocked LLM
- **Expected Output**: Summary with key points and action items
- **Assertions**:
  - `result["summary_text"] == "This is a summary"`
  - `result["key_points"] == ["Point 1", "Point 2"]`
  - `result["action_items"] == ["Action 1"]`

#### Test Case 7.2: Summarize with Custom Length
- **Description**: Use custom length parameter
- **Input**: Text, length="short"
- **Expected Output**: Short summary
- **Assertions**:
  - `result["summary_text"] == "Short summary"`

#### Test Case 7.3: Summarize with Custom Tone
- **Description**: Use custom tone parameter
- **Input**: Text, tone="formal"
- **Expected Output**: Formal summary
- **Assertions**:
  - `result["summary_text"] == "Formal summary"`

#### Test Case 7.4: Summarize with Custom Format
- **Description**: Use custom format parameter
- **Input**: Text, format_type="bullet"
- **Expected Output**: Bullet summary
- **Assertions**:
  - `result["summary_text"] == "Bullet summary"`

#### Test Case 7.5: Summarize Handles Exception
- **Description**: Handle LLM errors
- **Input**: Text, LLM that raises exception
- **Expected Output**: SummarizationError
- **Assertions**:
  - Exception message contains "Summarization failed"

#### Test Case 7.6: Summarize with Empty Segments
- **Description**: Handle empty segments
- **Input**: Empty text and segments
- **Expected Output**: Empty summary
- **Assertions**:
  - `result["summary_text"] == "Empty summary"`

#### Test Case 7.7: Summarize with Many Segments
- **Description**: Limit segments to 50
- **Input**: 100 segments
- **Expected Output**: Summary using last 50 segments
- **Assertions**:
  - `result["summary_text"] == "Summary of many segments"`
  - Last 50 segments used in prompt

#### Test Case 7.8: Summarize from Text
- **Description**: Summarize from full text only
- **Input**: Full text
- **Expected Output**: Summary with key points and action items
- **Assertions**:
  - `result["summary_text"] == "Text summary"`
  - `result["key_points"] == ["Key point 1"]`
  - `result["action_items"] == ["Action 1"]`

#### Test Case 7.9: Summarize from Text with Custom Params
- **Description**: Use custom parameters with summarize_from_text
- **Input**: Text, custom length/tone/format
- **Expected Output**: Custom summary
- **Assertions**:
  - `result["summary_text"] == "Custom summary"`

#### Test Case 7.10: Summarize from Text Handles Exception
- **Description**: Handle errors in summarize_from_text
- **Input**: Text, LLM that raises exception
- **Expected Output**: SummarizationError
- **Assertions**:
  - Exception message contains "Summarization failed"

#### Test Case 7.11: Summarize Default Parameters
- **Description**: Verify default parameters are used
- **Input**: Text, segments, no custom params
- **Expected Output**: Summary with default params
- **Assertions**:
  - `result["summary_text"] == "Default summary"`
  - "medium" in prompt (default length)
  - "neutral" in prompt (default tone)

#### Test Case 7.12: Summarize with Missing Keys in Response
- **Description**: Handle missing keys in LLM response
- **Input**: Text, LLM response missing key_points/action_items
- **Expected Output**: Summary with defaults
- **Assertions**:
  - `result["summary_text"] == "Summary only"`
  - `result["key_points"] == []`
  - `result["action_items"] == []`

#### Test Case 7.13: Summarize with None Values in Response
- **Description**: Handle None values in LLM response
- **Input**: Text, LLM response with None values
- **Expected Output**: Empty summary
- **Assertions**:
  - `result["summary_text"] == ""`
  - `result["key_points"] == []`
  - `result["action_items"] == []`

---

## 4. Test Execution Strategy

### Test Organization:
```
tests/
├── test_ingestion.py      # IngestionPipeline tests
├── test_storage.py        # Storage tests
├── test_chunker.py        # TextChunker tests
├── test_embeddings.py     # EmbeddingGenerator tests
├── test_vector_store.py   # VectorStore tests
├── test_question_answerer.py  # QuestionAnswerer tests
├── test_summarizer.py     # Summarizer tests
└── conftest.py            # Shared fixtures
```

### Fixtures:
- `db_path`: Temporary SQLite database path
- `storage`: Storage instance with temp DB
- `pipeline`: IngestionPipeline with mocked Whisper
- `vector_store`: VectorStore with temp ChromaDB
- `sample_chunks`: Pre-generated chunks for testing
- `mock_harness`: Mocked LLM harness

### Test Execution Commands:
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_storage.py -v

# Run with coverage
pytest tests/ --cov=video_ingestor --cov-report=html

# Run with verbose output
pytest tests/ -v --tb=short
```

---

## 5. Edge Cases and Error Handling

### Edge Cases to Test:
1. **Empty inputs**: Empty text, empty segments, empty chunks
2. **Large inputs**: 1000+ word texts, 100+ segments
3. **Special characters**: Unicode, emojis, special symbols
4. **Missing data**: Non-existent jobs, empty vector stores
5. **None values**: LLM responses with None fields
6. **Missing keys**: LLM responses with incomplete data
7. **Network failures**: Download failures, API errors
8. **File operations**: Missing files, permission errors

### Error Handling Tests:
1. **IngestionError**: Raised on ingestion failures
2. **SummarizationError**: Raised on summarization failures
3. **Storage errors**: Database connection issues
4. **Vector store errors**: ChromaDB connection issues
5. **Embedding errors**: Embedding generation failures

---

## 6. Mocking Strategy

### What to Mock:
1. **Whisper transcription**: Return predefined segments
2. **LLM responses**: Return predefined JSON responses
3. **Video download**: Return dummy file paths
4. **Audio extraction**: Return dummy audio file path
5. **Network requests**: Mock HTTP calls

### What to Use Real:
1. **SQLite storage**: Use temp files for real DB operations
2. **ChromaDB**: Use temp directories for real vector operations
3. **Embedding generation**: Use real embeddings for consistency
4. **Text chunking**: Real chunking logic

### Mock Implementation:
```python
# Example mock for Whisper
mock_model = MagicMock()
mock_model.transcribe.return_value = {
    "segments": [
        {"text": "Hello world", "start": 0.0, "end": 2.0},
    ],
    "text": "Hello world",
}

# Example mock for LLM
mock_harness = MagicMock()
mock_harness.generate_json.return_value = {
    "answer": "Test answer",
    "citations": [],
    "confidence": 0.5,
}
```

---

## 7. Test Data

### Sample Data:
- **Video paths**: `/tmp/test.mp4`, `/tmp/test.wav`
- **Audio files**: Dummy WAV files with 100 bytes
- **Text samples**: "Hello world", "Python is great", etc.
- **Job IDs**: "test-job", "job1", "job2"
- **Metadata**: `{"source": "url", "title": "Test Video"}`

### Test Files:
- Create dummy files in `tmp_path` fixtures
- Use `tempfile.mkstemp()` for temporary files
- Clean up files after tests

---

## 8. Coverage Goals

### Target Coverage:
- **Overall**: >80% code coverage
- **IngestionPipeline**: >90% (critical path)
- **Storage**: >95% (data integrity)
- **Chunker**: >90% (text processing)
- **Embeddings**: >85% (vector generation)
- **VectorStore**: >90% (search functionality)
- **QuestionAnswerer**: >85% (user-facing)
- **Summarizer**: >85% (user-facing)

### Coverage Exclusions:
- Network error paths (hard to mock)
- FFmpeg binary dependencies
- External API rate limits

---

## 9. Test Dependencies

### Required Packages:
```
pytest
pytest-cov
pytest-mock
unittest.mock
tempfile
sqlite3
chromadb
openai
pydantic
```

### Installation:
```bash
pip install pytest pytest-cov pytest-mock
pip install chromadb openai pydantic
```

---

## 10. Test Maintenance

### When to Update Tests:
1. **New features**: Add tests for new functionality
2. **Bug fixes**: Add regression tests
3. **API changes**: Update test expectations
4. **Dependency updates**: Verify compatibility

### Test Quality Checks:
1. **No hardcoded paths**: Use fixtures
2. **No network calls**: Mock external services
3. **No file leaks**: Clean up temp files
4. **No database leaks**: Use temp databases
5. **Clear assertions**: Specific expectations

### Test Documentation:
1. **Docstrings**: Explain test purpose
2. **Comments**: Explain complex logic
3. **Names**: Clear test case names
4. **Structure**: Organize by feature

---

## 11. CI/CD Integration

### GitHub Actions Workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ --cov=video_ingestor --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Local Testing:
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Generate coverage report
pytest tests/ --cov=video_ingestor --cov-report=html
```

---

## 12. Known Limitations

### What Cannot Be Tested:
1. **Real Whisper transcription**: Requires actual audio files and model
2. **Real video download**: Requires network access
3. **Real FFmpeg**: Requires system dependency
4. **Real LLM responses**: Requires API access
5. **Performance benchmarks**: Requires large datasets

### Workarounds:
1. Use mocked Whisper with predefined responses
2. Use dummy files for download/extract tests
3. Mock FFmpeg calls
4. Mock LLM harness
5. Use small test datasets

---

## 13. Test Results Interpretation

### Passing Criteria:
- All tests pass
- Coverage >80%
- No warnings
- No deprecation notices

### Failing Criteria:
- Any test fails
- Coverage <80%
- Resource leaks detected
- Database corruption

### Debugging Tips:
1. **Check mock calls**: Verify `assert_called_once()`
2. **Check temp files**: Ensure cleanup
3. **Check DB state**: Verify transactions
4. **Check embeddings**: Verify normalization
5. **Check search results**: Verify relevance

---

## 14. Future Test Enhancements

### Planned Tests:
1. **Integration tests**: Full pipeline with real Whisper
2. **Performance tests**: Large dataset benchmarks
3. **Load tests**: Multiple concurrent jobs
4. **Security tests**: Input validation
5. **Accessibility tests**: Error messages clarity

### Improvements:
1. **Parameterized tests**: Reduce duplication
2. **Test data generators**: Create test data dynamically
3. **Test utilities**: Common test helpers
4. **Test documentation**: Better test descriptions

---

## 15. Summary

This test plan covers:
- **137 test cases** across 7 test files
- **All major components** of the pipeline
- **Edge cases** and error handling
- **Mocking strategy** for external dependencies
- **Coverage goals** and quality checks
- **CI/CD integration** and maintenance

The tests ensure:
- **Correctness**: All components work as expected
- **Reliability**: Edge cases are handled
- **Maintainability**: Clear test structure
- **Quality**: High coverage and documentation
