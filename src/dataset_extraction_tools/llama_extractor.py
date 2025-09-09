"""
LlamaCloud-based document processing and structured data extraction.
Alternative implementation using LlamaParse + LlamaExtract instead of Pandoc/Marker + Instructor.
"""

from pathlib import Path
from typing import Union, Optional, TypeVar, Type, List, Dict, Any
import json
import asyncio

try:
    from llama_cloud_services import LlamaParse, LlamaExtract
    from pydantic import BaseModel
    LLAMA_CLOUD_AVAILABLE = True
except ImportError:
    LLAMA_CLOUD_AVAILABLE = False

T = TypeVar('T', bound=BaseModel)


class LlamaCloudProcessor:
    """Unified processor using LlamaCloud services for document processing and extraction."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize LlamaCloud processor with API key."""
        if not LLAMA_CLOUD_AVAILABLE:
            raise ImportError("Install llama-cloud-services: pip install llama-cloud-services")
        
        self.api_key = api_key
        self.parser = LlamaParse(
            api_key=api_key,
            result_type="markdown",
            verbose=True,
            language="en"
        )
        self.extractor = LlamaExtract(api_key=api_key)


def convert_to_markdown(
    file_path: Union[str, Path],
    api_key: Optional[str] = None,
    preset: str = "agentic",  # "cost_effective", "agentic", "agentic_plus"
    save_markdown: bool = True
) -> str:
    """
    Parse document to markdown using LlamaParse.
    Alternative to convert_to_markdown() using LlamaCloud.
    """
    if not LLAMA_CLOUD_AVAILABLE:
        raise ImportError("Install llama-cloud-services: pip install llama-cloud-services")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Configure parser based on preset
    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        verbose=True,
        language="en",
        # Add preset-specific configurations
        premium_mode=(preset == "agentic_plus"),
        fast_mode=(preset == "cost_effective")
    )
    
    # Parse document
    result = parser.parse(str(file_path))
    markdown_documents = result.get_markdown_documents()
    
    # Combine all pages into single markdown
    markdown_content = "\n\n".join([doc.text for doc in markdown_documents])
    
    # Save markdown file
    if save_markdown:
        markdown_path = file_path.with_suffix('.md')
        markdown_path.write_text(markdown_content, encoding='utf-8')
    
    return markdown_content


def extract_from_file(
    file_path: Union[str, Path],
    schema: Type[T],
    api_key: Optional[str] = None,
    agent_name: Optional[str] = None,
    save_json: bool = True
) -> T:
    """
    Direct structured data extraction from document using LlamaExtract.
    Alternative to extract_from_file() using LlamaCloud.
    """
    if not LLAMA_CLOUD_AVAILABLE:
        raise ImportError("Install llama-cloud-services: pip install llama-cloud-services")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Initialize extractor
    extractor = LlamaExtract(api_key=api_key)
    
    # Create or get agent
    if agent_name is None:
        agent_name = f"{schema.__name__.lower()}-extractor"
    
    try:
        agent = extractor.get_agent(name=agent_name)
    except:
        # Create new agent if doesn't exist
        agent = extractor.create_agent(
            name=agent_name,
            data_schema=schema
        )
    
    # Extract data
    result = agent.extract(str(file_path))
    
    # Convert to Pydantic model instance
    extracted_data = schema.model_validate(result.data)
    
    # Save JSON
    if save_json:
        json_path = file_path.with_suffix('.json')
        json_data = extracted_data.model_dump()
        json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding='utf-8')
    
    return extracted_data


def extract_from_files(
    file_paths: List[Union[str, Path]],
    schema: Type[T],
    api_key: Optional[str] = None,
    agent_name: Optional[str] = None
) -> List[T]:
    """
    Extract structured data from multiple files using LlamaExtract batch processing.
    """
    if not LLAMA_CLOUD_AVAILABLE:
        raise ImportError("Install llama-cloud-services: pip install llama-cloud-services")
    
    # Validate files
    valid_paths = []
    for file_path in file_paths:
        file_path = Path(file_path)
        if file_path.exists():
            valid_paths.append(str(file_path))
    
    if not valid_paths:
        raise FileNotFoundError("No valid files found")
    
    # Initialize extractor
    extractor = LlamaExtract(api_key=api_key)
    
    # Create or get agent
    if agent_name is None:
        agent_name = f"{schema.__name__.lower()}-batch-extractor"
    
    try:
        agent = extractor.get_agent(name=agent_name)
    except:
        agent = extractor.create_agent(
            name=agent_name,
            data_schema=schema
        )
    
    # Queue batch extraction
    jobs = asyncio.run(agent.queue_extraction(valid_paths))
    
    # Wait for completion and collect results
    results = []
    for job in jobs:
        # Poll for completion (in production, you'd want proper async handling)
        while True:
            job_status = agent.get_extraction_job(job.id)
            if job_status.status == "completed":
                result = agent.get_extraction_run_for_job(job.id)
                extracted_data = schema.model_validate(result.data)
                results.append(extracted_data)
                break
            elif job_status.status == "failed":
                print(f"Job {job.id} failed")
                break
            
            # Wait before checking again
            asyncio.run(asyncio.sleep(2))
    
    return results


