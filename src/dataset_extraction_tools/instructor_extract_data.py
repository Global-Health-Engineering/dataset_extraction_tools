"""
Structured data extraction from markdown using Instructor with evidence tracking.
Handles: Markdown -> Structured Data (only)
"""

from pathlib import Path
from typing import Union, Optional, TypeVar, Type, List
import json

try:
    import instructor
    from pydantic import BaseModel
except ImportError:
    raise ImportError("Install dependencies: pip install instructor pydantic")

T = TypeVar('T', bound=BaseModel)


def extract_data_from_markdown(
    markdown_content: str,
    response_model: Type[T],
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None
) -> T:
    """
    Extract structured data from markdown content with evidence tracking.
    
    Args:
        markdown_content: Markdown content to extract from
        response_model: Pydantic model with WithEvidence fields
        provider: LLM provider (e.g., "ollama/llama3.2", "openai/gpt-4o") 
        api_key: API key for cloud providers (not needed for Ollama)
        
    Returns:
        Extracted data instance
        
    Example:
        >>> from tests.ethord.ethord_schema import Ethord
        >>> markdown = "# Project Title\nThis is about..."
        >>> result = extract_data_from_markdown(markdown, Ethord)
        >>> print(f"Title: {result.title.value}")
    """
    client = _get_instructor_client(provider, api_key)
    
    prompt = (
        f"Extract structured data from this document. "
        f"For each field, provide exact quoted evidence and confidence 0-1.\n\n"
        f"{markdown_content}"
    )
    
    return client.chat.completions.create(
        response_model=response_model,
        messages=[{"role": "user", "content": prompt}],
        max_retries=2
    )


def extract_data_from_markdown_files(
    markdown_files: List[Union[str, Path]],
    response_model: Type[T],
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None,
    save_json: bool = True
) -> T:
    """
    Extract structured data from multiple markdown files in a single LLM call.
    
    Args:
        markdown_files: List of markdown file paths
        response_model: Pydantic model with WithEvidence fields
        provider: LLM provider 
        api_key: API key for cloud providers
        save_json: Save results as JSON in same directory as first file
        
    Returns:
        Extracted data instance combining info from all files
    """
    if not markdown_files:
        raise ValueError("No markdown files provided")
    
    # Read and combine all markdown content
    combined_content = []
    valid_files = []
    
    for i, markdown_file in enumerate(markdown_files):
        markdown_path = Path(markdown_file)
        
        if not markdown_path.exists():
            print(f"⚠️  Skipping missing file: {markdown_path}")
            continue
            
        markdown_content = markdown_path.read_text(encoding='utf-8')
        combined_content.append(f"=== DOCUMENT {i+1}: {markdown_path.name} ===\n{markdown_content}")
        valid_files.append(markdown_path)
    
    if not combined_content:
        raise FileNotFoundError("No valid markdown files found")
    
    # Single LLM call with all documents
    full_content = "\n\n".join(combined_content)
    
    result = extract_data_from_markdown(
        full_content, response_model, provider, api_key
    )
    
    # Save JSON by default (use first file's directory)
    if save_json and valid_files:
        json_path = valid_files[0].with_suffix('.json')
        _save_extraction_result(result, json_path)
        print(f"💾 Saved combined extraction to: {json_path}")
    
    return result


def extract_data_from_markdown_file(
    markdown_file: Union[str, Path],
    response_model: Type[T],
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None,
    save_json: bool = True
) -> T:
    """
    Extract structured data from a single markdown file.
    
    Args:
        markdown_file: Path to markdown file
        response_model: Pydantic model with WithEvidence fields
        provider: LLM provider 
        api_key: API key for cloud providers
        save_json: Save results as JSON in same directory
        
    Returns:
        Extracted data instance
    """
    markdown_path = Path(markdown_file)
    
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")
    
    # Read markdown content
    markdown_content = markdown_path.read_text(encoding='utf-8')
    
    # Extract data
    result = extract_data_from_markdown(
        markdown_content, response_model, provider, api_key
    )
    
    # Save JSON by default
    if save_json:
        json_path = markdown_path.with_suffix('.json')
        _save_extraction_result(result, json_path)
        print(f"💾 Saved extraction to: {json_path}")
    
    return result


def _get_instructor_client(provider: str, api_key: Optional[str]):
    """Get Instructor client for provider."""
    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    return instructor.from_provider(provider, **kwargs)


def _save_extraction_result(result: BaseModel, json_path: Path):
    """Save extraction result to JSON with evidence."""
    data = {}
    
    for field_name, field_value in result.__dict__.items():
        if field_value and hasattr(field_value, 'value') and field_value.value is not None:
            data[field_name] = {
                'value': field_value.value,
                'evidence': field_value.evidence,
                'confidence': field_value.confidence
            }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python instructor_extract_data.py <markdown_file>")
        print("Extracts structured data from a markdown file")
        sys.exit(1)
    
    # Test with ethord schema
    from tests.ethord.ethord_schema import Ethord
    
    try:
        result = extract_data_from_markdown_file(sys.argv[1], Ethord)
        print("✅ Extraction successful")
        print(f"📋 Extracted {len([f for f in result.__dict__.values() if f and hasattr(f, 'value') and f.value])} fields")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        sys.exit(1)