import os
import re
from typing import List
import chromadb
import google.generativeai as genai
from pypdf import PdfReader
import embeddingfunctions as ef
from decorators import decorator_time_taken


# load_pdf -> split_text -> create_chroma_db -> load_chroma_collection -> get_relevant_passage (user query in same
# embeddings) ->  make_rag_prompt -> generate_answer

@decorator_time_taken
def generate_answer_user(query="what is my daughter's name"):
    db = load_chroma_collection(path="./storage",  # replace with path of your persistent directory
                                name="daily_dairy")  # replace with the collection name
    answer = generate_answer(db, query=query)
    if answer is None:
        return "Nothing Found"
    else:
        print(answer)
        return answer


@decorator_time_taken
def generate_answer(db, query):
    # retrieve top 3 relevant text chunks
    relevant_text = get_relevant_passage(query, db, n_results=1000)
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


def get_relevant_passage(query, db, n_results):
    passage = db.query(query_texts=[query], n_results=n_results)['documents'][0]
    return passage


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
    db = chroma_client.get_collection(name=name, embedding_function=ef.GeminiEmbeddingFunction())

    return db


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
    total_documents = collection.count()
    for i, d in enumerate(documents):
        collection.add(documents=d, ids=str(total_documents))
        total_documents += total_documents
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
    update_embeddings_new_text("My son's name is Vidyut Srivastava")
    update_embeddings_new_text("My name is Prashantak Srivastava")
    update_embeddings_new_text("My daughters's name is Shyla Srivastava")

    # load_and_create_embeddings()
    generate_answer_user()
