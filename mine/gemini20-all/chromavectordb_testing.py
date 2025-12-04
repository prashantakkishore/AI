import chromadb
import os
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# 1. Initialize the embedding function
# The model name defaults to 'models/embedding-001'
model_name="models/text-embedding-004"
google_ef = GoogleGenerativeAiEmbeddingFunction(model_name=model_name)

# 2. Initialize ChromaDB client (using a persistent client here)
client = chromadb.PersistentClient(path="./chroma_db")

# 3. Create a collection, specifying the embedding function
collection = client.get_or_create_collection(
    name="gemini_collection",
    embedding_function=google_ef
)

# 4. Add documents to the collection
documents = [
    "The sun rises in the east and sets in the west.",
    "The moon is Earth's only permanent natural satellite.",
    "Artificial intelligence is rapidly advancing in capabilities.",
    "Vector databases are essential for efficient similarity search.",
    "Gemini models can process text, images, and audio."
]
ids = [f"id{i}" for i in range(len(documents))]
try:
    collection.add(
        documents=documents,
        ids=ids
    )
except Exception as e:
    print(f"An unexpected error occurred: {e}")


print(f"Added {len(documents)} documents to the collection.")

# 5. Query the collection
query = "What powers AI?"
results = collection.query(
    query_texts=[query],
    n_results=1
)

print(f"\nQuery: {query}")
print(f"Relevant document found: {results['documents']}")
