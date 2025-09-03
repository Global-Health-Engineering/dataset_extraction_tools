"""
High-level pipeline functions for batch document processing.

This module provides simple functions for users to:
1. Convert all documents in a directory tree to markdown
2. Extract structured data from all markdowns in a directory tree

Usage:
    from src.core.pipeline import convert_documents, extract_from_markdowns
    
    # Convert all docs to markdown (saves .md files in same directories)
    convert_documents("my_documents/")
    
    # Extract data from all markdowns (saves .json files in same directories)  
    extract_from_markdowns("my_documents/", MySchema)
"""

from pathlib import Path
from typing import Union, Optional, Type, Dict, List

from .document_converter import convert_document_to_markdown
from .instructor_extract_data import extract_data_from_markdown_file, extract_data_from_markdown_files

try:
    from pydantic import BaseModel
    T = Type[BaseModel]
except ImportError:
    raise ImportError("Install dependencies: pip install pydantic")


def convert_documents(
    directory: Union[str, Path],
    supported_extensions: Optional[set] = None,
    skip_existing: bool = True
) -> Dict[str, str]:
    """
    Recursively convert all documents in a directory tree to markdown.
    Saves markdown files in the same directory as source documents.
    
    Args:
        directory: Root directory to search for documents
        supported_extensions: File extensions to convert (default: common formats)
        skip_existing: Skip conversion if .md file already exists
        
    Returns:
        Dict mapping source file paths to status ("converted", "skipped", "error")
        
    Example:
        >>> results = convert_documents("tests/ethord/ORD documents/")
        >>> print(f"Converted {len([r for r in results.values() if r == 'converted'])} documents")
    """
    if supported_extensions is None:
        supported_extensions = {'.pdf', '.docx', '.doc', '.html', '.htm', '.txt', 
                              '.rtf', '.odt', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    results = {}
    
    # Find all supported documents recursively
    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
            
        if file_path.suffix.lower() not in supported_extensions:
            continue
        
        # Skip if already converted
        markdown_path = file_path.with_suffix('.md')
        if skip_existing and markdown_path.exists():
            results[str(file_path)] = "skipped"
            continue
        
        print(f"🔄 Converting: {file_path.relative_to(directory)}")
        
        try:
            # Convert to markdown
            markdown_content = convert_document_to_markdown(file_path)
            
            # Save markdown in same directory
            markdown_path.write_text(markdown_content, encoding='utf-8')
            
            results[str(file_path)] = "converted"
            print(f"✅ Saved: {markdown_path.relative_to(directory)}")
            
        except Exception as e:
            results[str(file_path)] = f"error: {str(e)}"
            print(f"❌ Failed: {file_path.relative_to(directory)} - {e}")
    
    # Summary
    converted = len([r for r in results.values() if r == "converted"])
    skipped = len([r for r in results.values() if r == "skipped"]) 
    errors = len([r for r in results.values() if r.startswith("error")])
    
    print(f"\n📊 Conversion Summary:")
    print(f"   ✅ Converted: {converted}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Errors: {errors}")
    
    return results


def extract_from_markdown_list(
    markdown_files: List[Union[str, Path]],
    response_model: T,
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None
) -> T:
    """
    Extract structured data from multiple markdown files in a single LLM call.
    Combines all files and processes them together for better context.
    
    Args:
        markdown_files: List of markdown files to process together
        response_model: Pydantic model defining extraction schema
        provider: LLM provider for extraction
        api_key: API key for cloud providers
        
    Returns:
        Single extracted data instance combining info from all files
        
    Example:
        >>> from tests.ethord.ethord_schema import Ethord
        >>> files = ["doc1.md", "doc2.md", "doc3.md"]
        >>> result = extract_from_markdown_list(files, Ethord)
        >>> print(f"Title: {result.title.value}")
    """
    print(f"🔄 Processing {len(markdown_files)} files in single LLM call...")
    
    try:
        # Single LLM call with all files combined
        result = extract_data_from_markdown_files(
            markdown_files,
            response_model,
            provider=provider,
            api_key=api_key,
            save_json=True
        )
        
        # Count extracted fields
        extracted_fields = len([f for f in result.__dict__.values() 
                              if f and hasattr(f, 'value') and f.value is not None])
        
        print(f"✅ Extracted {extracted_fields} fields from {len(markdown_files)} combined files")
        return result
        
    except Exception as e:
        print(f"❌ Combined extraction failed: {e}")
        raise


def extract_from_markdowns(
    directory: Union[str, Path],
    response_model: T,
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None,
    skip_existing: bool = True
) -> Dict[str, str]:
    """
    Extract structured data from all markdown files in a directory tree.
    Saves JSON files in the same directory as markdown files.
    
    Args:
        directory: Root directory to search for markdown files
        response_model: Pydantic model defining extraction schema
        provider: LLM provider for extraction
        api_key: API key for cloud providers
        skip_existing: Skip extraction if .json file already exists
        
    Returns:
        Dict mapping markdown file paths to status ("extracted", "skipped", "error")
        
    Example:
        >>> from tests.ethord.ethord_schema import Ethord
        >>> results = extract_from_markdowns("tests/ethord/ORD documents/", Ethord)
        >>> print(f"Extracted {len([r for r in results.values() if r == 'extracted'])} files")
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    results = {}
    
    # Find all markdown files recursively
    for markdown_path in directory.rglob("*.md"):
        if not markdown_path.is_file():
            continue
        
        # Skip if already extracted
        json_path = markdown_path.with_suffix('.json')
        if skip_existing and json_path.exists():
            results[str(markdown_path)] = "skipped"
            continue
        
        print(f"🔄 Extracting: {markdown_path.relative_to(directory)}")
        
        try:
            # Extract structured data
            result = extract_data_from_markdown_file(
                markdown_path, 
                response_model, 
                provider=provider, 
                api_key=api_key,
                save_json=True  # Auto-save JSON
            )
            
            results[str(markdown_path)] = "extracted"
            
            # Count extracted fields
            extracted_fields = len([f for f in result.__dict__.values() 
                                  if f and hasattr(f, 'value') and f.value is not None])
            print(f"✅ Extracted {extracted_fields} fields from: {markdown_path.relative_to(directory)}")
            
        except Exception as e:
            results[str(markdown_path)] = f"error: {str(e)}"
            print(f"❌ Failed: {markdown_path.relative_to(directory)} - {e}")
    
    # Summary
    extracted = len([r for r in results.values() if r == "extracted"])
    skipped = len([r for r in results.values() if r == "skipped"])
    errors = len([r for r in results.values() if r.startswith("error")])
    
    print(f"\n📊 Extraction Summary:")
    print(f"   ✅ Extracted: {extracted}")
    print(f"   ⏭️  Skipped: {skipped}")
    print(f"   ❌ Errors: {errors}")
    
    return results


def process_documents_full_pipeline(
    directory: Union[str, Path],
    response_model: T,
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None
) -> tuple[Dict[str, str], Dict[str, str]]:
    """
    Full pipeline: convert documents to markdown, then extract structured data.
    
    Args:
        directory: Root directory containing documents
        response_model: Pydantic model for extraction
        provider: LLM provider
        api_key: API key for cloud providers
        
    Returns:
        Tuple of (conversion_results, extraction_results)
        
    Example:
        >>> from tests.ethord.ethord_schema import Ethord
        >>> conv_results, ext_results = process_documents_full_pipeline(
        ...     "tests/ethord/ORD documents/", 
        ...     Ethord,
        ...     provider="openai/gpt-5-nano-2025-08-07",
        ...     api_key=os.getenv("OPENAI_API_KEY")
        ... )
    """
    print("🚀 Starting full document processing pipeline...")
    print(f"📁 Directory: {directory}")
    print(f"📋 Schema: {response_model.__name__}")
    print(f"🤖 Provider: {provider}")
    
    # Stage 1: Convert documents to markdown
    print("\n" + "="*60)
    print("STAGE 1: CONVERTING DOCUMENTS TO MARKDOWN")
    print("="*60)
    
    conversion_results = convert_documents(directory)
    
    # Stage 2: Extract structured data from markdowns
    print("\n" + "="*60)
    print("STAGE 2: EXTRACTING STRUCTURED DATA")
    print("="*60)
    
    extraction_results = extract_from_markdowns(
        directory, response_model, provider, api_key
    )
    
    print("\n🎉 Full pipeline completed!")
    return conversion_results, extraction_results


if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pipeline.py convert <directory>")
        print("  python pipeline.py extract <directory>")
        print("  python pipeline.py extract-list <file1.md> <file2.md> ...")
        print("  python pipeline.py full <directory>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "convert":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        convert_documents(directory)
    
    elif command == "extract":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        from tests.ethord.ethord_schema import Ethord
        extract_from_markdowns(directory, Ethord)
    
    elif command == "extract-list":
        if len(sys.argv) < 3:
            print("extract-list requires at least one markdown file")
            sys.exit(1)
        markdown_files = sys.argv[2:]
        from tests.ethord.ethord_schema import Ethord
        result = extract_from_markdown_list(
            markdown_files, 
            Ethord,
            provider="openai/gpt-5-nano-2025-08-07",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        print(f"Combined extraction completed: {len([f for f in result.__dict__.values() if f and hasattr(f, 'value') and f.value])} fields")
    
    elif command == "full":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        from tests.ethord.ethord_schema import Ethord
        process_documents_full_pipeline(
            directory, 
            Ethord,
            provider="openai/gpt-5-nano-2025-08-07",
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)