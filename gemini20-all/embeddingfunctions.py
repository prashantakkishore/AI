import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings
import os


class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function using the Gemini AI API for document retrieval.

    This class extends the EmbeddingFunction class and implements the __call__ method
    to generate embeddings for a given set of documents using the Gemini AI API.

    Parameters:
    - input (Documents): A collection of documents to be embedded.

    Returns:
    - Embeddings: Embeddings generated for the input documents.
    """

    def __call__(self, input: Documents) -> Embeddings:
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise ValueError("Gemini API Key not provided. Please provide GOOGLE_API_KEY as an environment variable")
        genai.configure(api_key=gemini_api_key)
        model = "models/text-embedding-004"
        title = "Custom query"
        return genai.embed_content(model=model,
                                   content=input,
                                   task_type="retrieval_document",
                                   title=title)["embedding"]
