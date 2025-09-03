# marker-instructor

Document extraction pipeline: Document → Markdown → Structured Data with Evidence

## Quick Start

```bash
# Setup
source venv/bin/activate
pip install -e .

# Set API key
export OPENAI_API_KEY="your-key-here"
```

## Two-Stage Pipeline

**Stage 1: Document → Markdown**
- Supports: PDF (via Marker), DOCX/HTML (via Pandoc), images
- Auto-saves `.md` files in same directories

**Stage 2: Markdown → Structured Data**
- Uses Instructor + LLM for extraction with evidence tracking
- Auto-saves `.json` files with evidence and confidence scores

## Usage Examples

### Process ORD Documents
```python
from src.core.pipeline import convert_documents, extract_from_markdown_list
from tests.ethord.ethord_schema import Ethord
import os

# Convert all ORD documents to markdown
convert_documents("tests/ethord/ORD documents/")

# Extract from specific files (single LLM call)
result = extract_from_markdown_list([
    "tests/ethord/ORD documents/openjmp/document1.md",
    "tests/ethord/ORD documents/openjmp/document2.md"
], Ethord, provider="openai/gpt-5-nano-2025-08-07", api_key=os.getenv("OPENAI_API_KEY"))

print(f"Title: {result.title.value}")
print(f"Evidence: {result.title.evidence}")
```

### LLM Providers
- `"openai/gpt-5-nano-2025-08-07"` (requires OPENAI_API_KEY)
- `"ollama/llama3.2"` (local, no API key needed)
- `"anthropic/claude-3-5-sonnet"` (requires ANTHROPIC_API_KEY)

### Custom Schema
```python
from src.core.with_evidence import StringWithEvidence
from pydantic import BaseModel, Field

class MySchema(BaseModel):
    title: StringWithEvidence = Field(description="Document title")
```

## File Structure After Processing
```
documents/
├── proposal.pdf     # Original
├── proposal.md      # Generated markdown  
└── proposal.json    # Extracted data with evidence
```

## Architecture
- `src/core/document_converter.py` - Document → Markdown
- `src/core/instructor_extract_data.py` - Markdown → Structured Data  
- `src/core/pipeline.py` - Batch operations
- `tests/ethord/ethord_schema.py` - Example extraction schema