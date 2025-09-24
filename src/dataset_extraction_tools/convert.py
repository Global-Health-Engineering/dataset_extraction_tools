"""
Simple document to markdown converter using Pandoc with Marker fallback.

Two-stage processing:
1. Document -> Markdown (Pandoc for DOCX/HTML, Marker for PDF/images)
2. Markdown -> Structured Data (via Instructor)
"""

from pathlib import Path
from typing import Union
import logging
from .utils import timing

try:
    import pypandoc
    PANDOC_AVAILABLE = True
except ImportError:
    PANDOC_AVAILABLE = False

try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False

_EXTENSIONS_NOT_SUPPORTED_BY_PANDOC = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}

@timing
def convert_to_markdown(file_path: Union[str, Path], use_marker: bool = False, **converter_kwargs) -> str:
    """
    Convert document to markdown using Pandoc first, Marker fallback.
    
    Args:
        file_path: Path to document file
        use_marker: Force usage of Marker instead of Pandoc
        
    Returns:
        Markdown content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If conversion fails
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_ext = file_path.suffix.lower()
    
    # Force Marker usage if requested
    if use_marker:
        return _convert_with_marker(file_path, **converter_kwargs)
    
    # PDF and image formats -> Marker
    if file_ext in _EXTENSIONS_NOT_SUPPORTED_BY_PANDOC:
        return _convert_with_marker(file_path, **converter_kwargs)
    
    # Text formats -> Pandoc first, Marker fallback
    try:
        return _convert_with_pandoc(file_path)
    except Exception as e:
        logging.warning(f"Pandoc failed: {e}, trying Marker")
        return _convert_with_marker(file_path, **converter_kwargs)


def _convert_with_pandoc(file_path: Path) -> str:
    """Convert using Pandoc."""
    if not PANDOC_AVAILABLE:
        raise RuntimeError("pypandoc not available. Install with: pip install pypandoc-binary")
    
    return pypandoc.convert_file(
        str(file_path),
        'md',
        extra_args=['--wrap=none', '--markdown-headings=atx']
    )


def _convert_with_marker(file_path: Path, **kwargs) -> str:
    """Convert using Marker."""
    if not MARKER_AVAILABLE:
        raise RuntimeError("marker-pdf not available. Install with: pip install marker-pdf[full]")

    # Set defaults
    defaults = {
        "output_format": "markdown"
    }
    
    # Update with provided kwargs
    config = {**defaults, **kwargs}

    config_parser = ConfigParser(config)
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
        llm_service=config_parser.get_llm_service()
    )
    
    # Convert document
    rendered = converter(str(file_path))
    
    if not rendered or not hasattr(rendered, 'markdown'):
        raise RuntimeError("Marker conversion failed")
    
    return rendered.markdown