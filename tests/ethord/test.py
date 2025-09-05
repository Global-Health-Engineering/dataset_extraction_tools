import dataset_extraction_tools.document_converter as det
import os

det.convert_document_to_markdown(os.path.join("tests",
                                   "ethord",
                                   "ORD files - 20250826 - public",
                                   "Explore - 26.08.25",
                                   "Tilley - 2nd call",
                                   "application",
                                   "Application-PDF-ORD-call.pdf"),
                      use_llm = True,
                      llm_service = "marker.services.openai.OpenAIService",
                      api_key=os.getenv("OPENAI_API_KEY"),
                      model="gpt-5-nano-2025-08-07")