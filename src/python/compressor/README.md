# BillBuster Compressor

A library for processing legislative documents and bills to extract key points using LLMs with langchain.

## Overview

This library takes text or PDF files containing legislative documents (bills, laws, etc.) and uses Large Language Models (LLMs) to extract key points about what the legislation does. It handles:

- Reading and chunking large documents
- Maintaining context across document chunks with a sliding memory window
- Using LLMs to extract specific legislative points
- Categorizing points by type (funding, changes, requirements, etc.)
- Pushing points to a queue for further processing

## Components

- **DocumentChunker**: Splits large documents into manageable chunks
- **PointExtractor**: Uses LLMs to analyze text and extract key points
- **SlidingMemory**: Maintains context across document chunks
- **QueueManager**: Handles the queue of extracted points
- **DocumentProcessor**: Orchestrates the entire process

## Usage

```python
from compressor import DocumentProcessor
import os

# Initialize the processor
processor = DocumentProcessor(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-4-turbo"  # or gpt-3.5-turbo for lower cost
)

# Process a document
points, stats = processor.process_document("/path/to/bill.pdf")

# Save points to a file
processor.save_points_to_file("/path/to/output.json")
```

## Point Format

Each extracted point contains:

```json
{
  "point_type": "funding",  // One of: funding, change, classification, requirement, permission, timeline, penalty, other
  "description": "Allocates $10 million for renewable energy research",
  "entities": ["Department of Energy", "research institutions"],
  "reference": "Section 102(a)",
  "confidence": "high",
  "document_path": "/path/to/bill.pdf",
  "document_name": "bill.pdf",
  "chunk_index": 3
}
```

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies: langchain, openai, PyPDF2, etc. (see requirements.txt)

## Example

See `example.py` for a complete working example.