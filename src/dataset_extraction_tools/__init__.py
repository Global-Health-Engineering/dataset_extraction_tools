"""
Dataset Extraction Tools - Simplified API
Extract datasets from documents: Document -> Markdown -> Structured Data with Evidence
"""

# Core conversion and extraction
from .convert import convert_to_markdown
from .extract import (
    extract_from_text, extract_from_file, extract_from_files,
    WithEvidence, StringWithEvidence, IntWithEvidence, 
    FloatWithEvidence, DateWithEvidence, EnumWithEvidence
)

# Batch processing
from .core import (
    convert_dir, extract_dir
)

__all__ = [
    # Single document processing
    "convert_to_markdown",
    "extract_from_text", 
    "extract_from_file",
    "extract_from_files",
    
    # Batch processing
    "convert_dir",
    "extract_dir", 
    
    # Evidence models
    "WithEvidence",
    "StringWithEvidence",
    "IntWithEvidence", 
    "FloatWithEvidence",
    "DateWithEvidence",
    "EnumWithEvidence",

    # Utils
    "find_files",
    "status_dir",
    "clean_dir"
]