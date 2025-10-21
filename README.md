# dataset_extraction_tools

Extract datasets from documents pipeline: Document → Markdown → Structured Data with Evidence

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
- Supports: PDF (via Marker/Docling), DOCX/HTML (via Pandoc/Docling), images
- Backends: Pandoc (text formats), Marker (PDF/images), Docling (all formats)
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

# Convert all ORD documents to markdown (default: Pandoc → Marker fallback)
convert_documents("tests/ethord/ORD documents/")

# Convert using Docling for better table extraction
convert_documents("tests/ethord/ORD documents/", use_docling=True)

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

### Docling Backend Usage
```python
from dataset_extraction_tools.convert import convert_to_markdown

# Use Docling for any document format
markdown = convert_to_markdown("document.pdf", use_docling=True)

# Configure Docling for better table extraction
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Advanced Docling configuration
format_options = {
    InputFormat.PDF: PdfFormatOption(
        pipeline_options=PdfPipelineOptions(
            do_table_structure=True,  # Enhanced table extraction
            generate_page_images=True,  # For visual grounding
            images_scale=2.0,
        )
    )
}

markdown = convert_to_markdown(
    "complex_document.pdf",
    use_docling=True,
    format_options=format_options
)
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