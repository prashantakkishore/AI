from chromadb import Documents, EmbeddingFunction, Embeddings
from client_config import client
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
        model = "models/text-embedding-004"
        title = "Custom query"

        # Use the client object's models.embed_content method
        return client.models.embed_content(
            model=model,
            content=input,
            task_type="retrieval_document",
            title=title
        )["embedding"]
