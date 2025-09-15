"""
Simplified batch processing pipeline for document conversion and extraction.
Consolidates all batch operations with unified file discovery and error handling.
"""

import logging
from pathlib import Path
from typing import Union, Optional, Type, Dict, List, Set
from .convert import convert_to_markdown, _EXTENSIONS_NOT_SUPPORTED_BY_PANDOC
from .extractor import extract_from_file, T
from .utils import timing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def find_files(directory: Union[str, Path], extensions: Set[str], recursive: bool = True) -> List[Path]:
    """File discovery in directory given a list of allowed extensions."""
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    pattern = "**/*" if recursive else "*"
    return [
        f for f in directory.glob(pattern) 
        if f.is_file() and f.suffix.lower() in extensions
    ]


@timing
def convert_dir(
    directory: Union[str, Path],
    file_types: Optional[List[str]] = None,
    skip_existing: bool = True,
    **converter_kwargs
) -> Dict[str, str]:
    """Convert all documents in directory to markdown."""
    if file_types is None:
        file_types = [ext.lstrip('.') for ext in _EXTENSIONS_NOT_SUPPORTED_BY_PANDOC]
    
    extensions = {f".{ext}" for ext in file_types}
    files = find_files(directory, extensions)
    results = {}
    
    for file_path in files:
        logger.info(f"Processing file: {file_path}")
        markdown_path = file_path.with_suffix('.md')
        
        if skip_existing and markdown_path.exists():
            logger.info(f"Skipping existing file: {file_path}")
            results[str(file_path)] = "skipped"
            continue
        
        try:
            markdown_content = convert_to_markdown(file_path, **converter_kwargs)
            markdown_path.write_text(markdown_content, encoding='utf-8')
            logger.info(f"Successfully converted file: {file_path}")
            results[str(file_path)] = "converted"
        except Exception as e:
            logger.error(f"Error converting file {file_path}: {str(e)}")
            results[str(file_path)] = f"error: {str(e)}"
    
    return results


@timing
def extract_dir(
    directory: Union[str, Path],
    response_model: Type[T],
    skip_existing: bool = True,
    **extractor_kwargs
) -> Dict[str, str]:
    """Extract structured data from all markdown files in directory."""
    markdown_files = find_files(directory, {".md"})
    results = {}
    
    for markdown_path in markdown_files:
        logger.info(f"Processing file: {markdown_path}")
        json_path = markdown_path.with_suffix('.json')
        
        if skip_existing and json_path.exists():
            logger.info(f"Skipping existing file: {markdown_path}")
            results[str(markdown_path)] = "skipped"
            continue
        
        try:
            extract_from_file(markdown_path, response_model, **extractor_kwargs)
            logger.info(f"Successfully extracted from file: {markdown_path}")
            results[str(markdown_path)] = "extracted"
        except Exception as e:
            logger.error(f"Error extracting from file {markdown_path}: {str(e)}")
            results[str(markdown_path)] = f"error: {str(e)}"
    
    return results


@timing
def process_dir(
    directory: Union[str, Path],
    response_model: Type[T],
    file_types: Optional[List[str]] = None,
    **kwargs
) -> tuple[Dict[str, str], Dict[str, str]]:
    """Full pipeline: convert documents to markdown, then extract structured data."""
    converter_kwargs = {k: v for k, v in kwargs.items() if k in ['use_llm', 'llm_service', 'api_key', 'model']}
    extractor_kwargs = {k: v for k, v in kwargs.items() if k in ['provider', 'api_key', 'save_json']}
    
    conversion_results = convert_dir(directory, file_types, **converter_kwargs)
    extraction_results = extract_dir(directory, response_model, **extractor_kwargs)
    
    return conversion_results, extraction_results

