"""
Simplified batch processing pipeline for document conversion and extraction.
Consolidates all batch operations with unified file discovery and error handling.
"""

import logging
from pathlib import Path
from typing import Union, Optional, Type, Dict, List
from .convert import convert_to_markdown, _EXTENSIONS_NOT_SUPPORTED_BY_PANDOC
from .extract import extract_from_file, T
from .utils import timing, find_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


@timing
def convert_dir(
    directory: Union[str, Path],
    file_types: Optional[List[str]] = None,
    skip_existing: bool = True,
    path_filter: str = None,
    **converter_kwargs
) -> Dict[str, str]:
    """Convert all documents in directory to markdown."""
    if file_types is None:
        file_types = [ext.lstrip('.') for ext in _EXTENSIONS_NOT_SUPPORTED_BY_PANDOC]
    
    extensions = {f".{ext}" for ext in file_types}
    files = find_files(directory, extensions, recursive=True, path_filter=path_filter)
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
    path_filter: str = None,
    **extractor_kwargs
) -> Dict[str, str]:
    """Extract structured data from all markdown files in directory."""
    markdown_files = find_files(directory, {".md"}, recursive=True, path_filter=path_filter)
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
def status_dir(
    directory: Union[str, Path],
    file_types: Optional[List[str]] = None,
    path_filter: str = None
) -> Dict[str, int]:
    """Count total files vs converted markdown files and extracted JSON files in directory.
    
    Args:
        directory: Directory to analyze
        file_types: List of file extensions to consider (without dots)
                   If None, uses default conversion extensions
    
    Returns:
        Dictionary with conversion and extraction statistics
    """
    if file_types is None:
        file_types = [ext.lstrip('.') for ext in _EXTENSIONS_NOT_SUPPORTED_BY_PANDOC]
    
    extensions = {f".{ext}" for ext in file_types}
    total_files = find_files(directory, extensions, recursive=True, path_filter=path_filter)
    markdown_files = find_files(directory, {".md"}, recursive=True, path_filter=path_filter)
    
    converted_count = 0
    for file_path in total_files:
        markdown_path = file_path.with_suffix('.md')
        if markdown_path.exists():
            converted_count += 1
    
    extracted_count = 0
    for markdown_path in markdown_files:
        json_path = markdown_path.with_suffix('.json')
        if json_path.exists():
            extracted_count += 1
    
    stats = {
        'total_source_files': len(total_files),
        'converted_to_md': converted_count,
        'total_md_files': len(markdown_files),
        'extracted_to_json': extracted_count,
        '% converted': round(converted_count/len(total_files)*100, 1) if total_files else 0,
        '% extracted': round(extracted_count/len(markdown_files)*100, 1) if markdown_files else 0
    }
    
    print(f"Directory status for {directory}:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return stats


@timing
def clean_dir(
    directory: Union[str, Path],
    file_types: Optional[List[str]] = None,
    path_filter: str = None
) -> Dict[str, str]:
    """Delete files with specified extensions.

    Args:
        directory: Directory to clean
        file_types: List of file extensions to delete (without dots)
                   If None, uses default conversion extensions

    Returns:
        Dictionary with deletion results for each file
    """
    if file_types is None:
        file_types = [ext.lstrip('.') for ext in _EXTENSIONS_NOT_SUPPORTED_BY_PANDOC]

    extensions = {f".{ext}" for ext in file_types}
    target_files = find_files(directory, extensions, recursive=True, path_filter=path_filter)
    results = {}

    for target_file in target_files:
        try:
            target_file.unlink()
            logger.info(f"Deleted file: {target_file}")
            results[str(target_file)] = "deleted"
        except Exception as e:
            logger.error(f"Error deleting file {target_file}: {str(e)}")
            results[str(target_file)] = f"error: {str(e)}"

    return results
