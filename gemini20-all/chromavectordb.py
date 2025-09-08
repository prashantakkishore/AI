import os
import re
from typing import List
import chromadb
import google.generativeai as genai
from pypdf import PdfReader
import embeddingfunctions as ef
from decorators import decorator_time_taken
import datetime
import util


# load_pdf -> split_text -> create_chroma_db -> load_chroma_collection -> get_relevant_passage (user query in same
# embeddings) ->  make_rag_prompt -> generate_answer

@decorator_time_taken
def generate_answer_user(date, query="what is my daughter's name"):
    db = load_chroma_collection(path="./storage",  # replace with path of your persistent directory
                                name="daily_dairy")  # replace with the collection name
    answer = generate_answer(date, db, query=query)
    if answer is None:
        return "Nothing Found"
    else:
        print(answer)
        return answer


@decorator_time_taken
def generate_answer(date, collection, query):
    # retrieve top 3 relevant text chunks
    relevant_text = get_relevant_passage(date, query, collection, n_results=1000)
    prompt = make_rag_prompt(query,
                             relevant_passage="".join(
                                 relevant_text))  # joining the relevant chunks to create a single passage
    answer = generate_answer_gemini(prompt)

    return answer


def generate_answer_gemini(prompt):
    gemini_api_key = os.getenv("GOOGLE_API_KEY")
    if not gemini_api_key:
        raise ValueError("Gemini API Key not provided. Please provide GOOGLE_API_KEY as an environment variable")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    answer = model.generate_content(prompt)
    return answer.text


def make_rag_prompt(query, relevant_passage):
    escaped = relevant_passage.replace("'", "").replace('"', "").replace("\n", " ")
    prompt = ("""You are a helpful and informative bot that answers questions using text from the reference passage 
    included below. Be sure to respond in a complete sentence, being comprehensive, including all relevant 
    background information. However, you are talking to a non-technical audience, so be sure to break down 
    complicated concepts and strike a friendly and conversational tone. If the passage is irrelevant to the 
    answer, you may ignore it. QUESTION: '{query}' PASSAGE: '{relevant_passage}'

  ANSWER:
  """).format(query=query, relevant_passage=escaped)

    return prompt


def get_relevant_passage(date, query, collection, n_results):
    if date:
        real_date = util.fuzzy_date_to_date(date)  # converts today, tomorrow to real date
        if real_date:
            return get_relevant_passage_timestamp(real_date, query, collection, n_results)

    results = collection.query(query_texts=[query], n_results=n_results, where={"date": ""})
    if results and 'documents' in results and results['documents']:
        passage = results['documents'][0]
    else:
        passage = []

    print(f"Getting all data as no date is given passage {passage}")
    return passage


def get_relevant_passage_timestamp(date, query, collection, n_results):
    """Retrieves relevant passages from the Chroma collection based on a specific date and query.

    Args:
        date (str): The date to filter the passages by (in ISO format, e.g., 'YYYY-MM-DD').
        query (str): The query string to search for relevant passages.
        collection (chromadb.Collection): The Chroma collection to search within.
        n_results (int): The maximum number of results to return.  It's effectively ignored here since Chroma's
                         filtering mechanism can return more or less than `n_results`.  You may want to use it
                         to limit the *overall* number of returned documents if Chroma's internal filtering is too broad.

    Returns:
        List[str]: A list of relevant passages (strings) that match the date and query.  Returns an empty list
                     if no matching passages are found.
    """
    print(f"Getting date specific data as date is given {date}")

    results = collection.query(
        query_texts=[query],
        n_results=n_results,  # Keep n_results for a general limit on results. Important for performance
        where={"date": str(date)}
    )

    print(f"Chroma query results: {results}")  # Debug: Inspect the full query result

    if results and 'documents' in results and results['documents']:
        passages = results['documents'][0]  # Access the *first* list of documents. Corrected line!
        print(f"Found passages for date {date}: {passages}")
        return passages
    else:
        print(f"No passages found for date {date}.")
        return [] # Return an empty list if no matching documents are found.  This is crucial.


def load_chroma_collection(path, name):
    """
    Loads an existing Chroma collection from the specified path with the given name.

    Parameters:
    - path (str): The path where the Chroma database is stored.
    - name (str): The name of the collection within the Chroma database.

    Returns:
    - chromadb.Collection: The loaded Chroma Collection.
    """
    chroma_client = chromadb.PersistentClient(path=path)
    collection = chroma_client.get_collection(name=name, embedding_function=ef.GeminiEmbeddingFunction())

    return collection


def create_chroma_db(documents: List, path: str, name: str):
    """
    Creates a Chroma database using the provided documents, path, and collection name.

    Parameters:
    - documents: An iterable of documents to be added to the Chroma database.
    - path (str): The path where the Chroma database will be stored.
    - name (str): The name of the collection within the Chroma database.

    Returns:
    - Tuple[chromadb.Collection, str]: A tuple containing the created Chroma Collection and its name.
    """
    chroma_client = chromadb.PersistentClient(path=path)
    collection = chroma_client.get_or_create_collection(name=name, embedding_function=ef.GeminiEmbeddingFunction())
    # collection = chroma_client.create_collection(name=name, embedding_function=ef.GeminiEmbeddingFunction())
    today_date = datetime.datetime.now().date().isoformat()   # Convert to Unix timestamp for efficient storage
    timestamp = int(datetime.datetime.now().timestamp())
    collection.add(
        documents=documents,
        metadatas=[{"date": str(today_date), "user_id": ""}],  # add user later
        ids=[str(timestamp)]  # Using timestamp as ID for simplicity
    )

    return collection, name


def load_pdf(file_path):
    """
    Reads the text content from a PDF file and returns it as a single string.

    Parameters:
    - file_path (str): The file path to the PDF file.

    Returns:
    - str: The concatenated text content of all pages in the PDF.
    """
    # Logic to read pdf
    reader = PdfReader(file_path)

    # Loop over each page and store it in a variable
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    return text


def split_text(text: str):
    """
    Splits a text string into a list of non-empty substrings based on the specified pattern.
    The "\n \n" pattern will split the document para by para
    Parameters:
    - text (str): The input text to be split.

    Returns:
    - List[str]: A list containing non-empty substrings obtained by splitting the input text.

    """
    splitted_text = re.split('\n \n', text)
    return [i for i in splitted_text if i != ""]


def update_embeddings_new_text(text):
    chunked_text = split_text(text)
    print(chunked_text)
    create_chroma_db(documents=chunked_text,
                     path="./storage",
                     name="daily_dairy")


def load_and_create_embeddings():
    # pdf_text = load_pdf("./downloads/prashantak_srivastava_usa.pdf")
    pdf_text = load_pdf("./downloads/Srivastava,Prashantak_payslip.pdf")
    chunked_text = split_text(pdf_text)
    print(chunked_text)
    create_chroma_db(documents=chunked_text,
                     path="./storage",
                     name="daily_dairy")


if __name__ == "__main__":
    # First, clear out the ChromaDB directory (for testing purposes)
    # import shutil
    # if os.path.exists("./storage"):
    #     shutil.rmtree("./storage")

    # Add some test data for today and yesterday
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    timestamp = int(datetime.datetime.now().timestamp())
    #create chroma db
    chroma_client = chromadb.PersistentClient(path="./storage")
    collection = chroma_client.get_or_create_collection(name="daily_dairy", embedding_function=ef.GeminiEmbeddingFunction())

    # collection.add(
    #     documents=["My name is Prashantak Srivastava"],
    #     metadatas=[{"date": "", "user_id": ""}],
    #     ids=[str(timestamp + 1)]
    # )
    # collection.add(
    #     documents=["My daughters name is Shyla Srivastava"],
    #     metadatas=[{"date": "", "user_id": ""}],
    #     ids=[str(timestamp + 2)]
    # )
    #
    # collection.add(
    #     documents=["Shyla's birth day is November 16th"],
    #     metadatas=[{"date": "", "user_id": ""}],
    #     ids=[str(timestamp + 3)]
    # )
    #
    # collection.add(
    #     documents=["I walked 12000 steps"],
    #     metadatas=[{"date": "03/11/2025", "user_id": ""}],
    #     ids=[str(timestamp + 4)]
    # )
    # collection.add(
    #     documents=["I had great cricket match and we won both the games"],
    #     metadatas=[{"date": yesterday, "user_id": ""}],
    #     ids=[str(timestamp + 5)]
    # )


    # Test querying for yesterday's data
    # answer = generate_answer_user("yesterday", query="all notes")
    # print(f"Answer for yesterday: {answer}")

    # Test querying for today's data
    answer = generate_answer_user("", query="My daughter's name")
    print(f"Answer for today: {answer}")