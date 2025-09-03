"""
Simple document to markdown converter using Pandoc with Marker fallback.

Two-stage processing:
1. Document -> Markdown (Pandoc for DOCX/HTML, Marker for PDF/images)
2. Markdown -> Structured Data (via Instructor)
"""

from pathlib import Path
from typing import Union, Optional, Dict, Any
import logging

try:
    import pypandoc
    PANDOC_AVAILABLE = True
except ImportError:
    PANDOC_AVAILABLE = False

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False


def convert_document_to_markdown(file_path: Union[str, Path]) -> str:
    """
    Convert document to markdown using Pandoc first, Marker fallback.
    
    Args:
        file_path: Path to document file
        
    Returns:
        Markdown content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If conversion fails
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_ext = file_path.suffix.lower().lstrip('.')
    
    # PDF and image formats -> Marker
    if file_ext in {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}:
        return _convert_with_marker(file_path)
    
    # Text formats -> Pandoc first, Marker fallback
    try:
        return _convert_with_pandoc(file_path)
    except Exception as e:
        logging.warning(f"Pandoc failed: {e}, trying Marker")
        return _convert_with_marker(file_path)


def _convert_with_pandoc(file_path: Path) -> str:
    """Convert using Pandoc."""
    if not PANDOC_AVAILABLE:
        raise RuntimeError("pypandoc not available. Install with: pip install pypandoc-binary")
    
    return pypandoc.convert_file(
        str(file_path),
        'gfm',
        extra_args=['--wrap=none', '--markdown-headings=atx']
    )


def _convert_with_marker(file_path: Path) -> str:
    """Convert using Marker."""
    if not MARKER_AVAILABLE:
        raise RuntimeError("marker-pdf not available. Install with: pip install marker-pdf[full]")
    
    # Initialize converter
    artifact_dict = create_model_dict()
    converter = PdfConverter(artifact_dict=artifact_dict)
    
    # Convert document
    rendered = converter(str(file_path))
    
    if not rendered or not hasattr(rendered, 'markdown'):
        raise RuntimeError("Marker conversion failed")
    
    return rendered.markdown


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python document_converter.py <file_path>")
        sys.exit(1)
    
    try:
        markdown = convert_document_to_markdown(sys.argv[1])
        print("✅ Conversion successful")
        print(f"📄 Output length: {len(markdown)} characters")
        print("\n" + "="*50 + " MARKDOWN OUTPUT " + "="*50)
        print(markdown)
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        sys.exit(1)