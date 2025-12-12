import chromadb
import os
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from the .env file
load_dotenv()

DB="./storage"
COLLECTION="daily_dairy"

# 1. Initialize the embedding function
# The model name defaults to 'models/embedding-001'
model_name="models/text-embedding-004"
google_ef = GoogleGenerativeAiEmbeddingFunction(model_name=model_name)

# 2. Initialize ChromaDB client (using a persistent client here)
client = chromadb.PersistentClient(path=DB)

# 3. Create a collection, specifying the embedding function
collection = client.get_or_create_collection(
    name=COLLECTION,
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
        metadatas=[
            {"date": "03/11/2025", "user_id": "aa1"},
            {"date": "04/11/2025", "user_id": "aa2"},
            {"date": "05/11/2025", "user_id": "aa3"},
            {"date": "06/11/2025", "user_id": "aa4"},
            {"date": "07/11/2025", "user_id": "aa5"}
        ],
        ids=ids
    )
except Exception as e:
    print(f"An unexpected error occurred: {e}")


print(f"Added {len(documents)} documents to the collection.")

# 5. Query the collection
query = "What Gemini models can provide?"
results = collection.query(
    query_texts=[query],
    n_results=1
)

print(f"\nQuery: {query}")
print(f"Relevant document found: {results['documents']}")



def print_docs_in_collection():
    # Retrieve all documents (setting limit to a high number or total count)
    # A robust way is to get the count first, then set the limit to that count
    try:
        count = collection.count()
        all_documents_data = collection.get(
            limit=count,
            include=["metadatas", "documents", "embeddings"] # Specify what data to include
        )

        print(f"Retrieved {len(all_documents_data['documents'])} documents:")

        for i, doc in enumerate(all_documents_data['documents']):
            metadata = all_documents_data['metadatas'][i]
            doc_id = all_documents_data['ids'][i]
            print(f"\n--- Document ID: {doc_id} ---")
            print(f"Content: {doc}")
            print(f"Metadata: {metadata}")

    except Exception as e:
        print(f"An error occurred: {e}")


def print_get_all_collections():
    # List all collections
    collections = client.list_collections()

    # Print the names of the collections
    print("Available ChromaDB Collections:")
    for collection_name in collections:
        print(collection_name)
    return collections

print_docs_in_collection()