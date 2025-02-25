

import requests
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from decorators import decorator_time_taken
import chromavectordb as cvd

gemini_embedding_model = GeminiEmbedding(model_name="models/text-embedding-004")
llm = Gemini(model_name="models/gemini-2.0-flash-exp")


@decorator_time_taken
def write_to_diary(notes):
    cvd.update_embeddings_new_text(notes)
    return "Saved to diary"


# Define the tool (function)
write_to_diary_tool = {
    "function_declarations": [
        {
            "name": "write_to_diary",
            "description": "This is a personal daily diary and use this tool to write notes to the diary or take notes",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "notes": {
                        "type": "STRING",
                        "description": "The notes string to write to the diary"
                    }
                },
                "required": ["notes"]
            }
        }
    ]
}


@decorator_time_taken
def find_in_diary(query):
    return cvd.generate_answer_user(query=query)


# Define the tool (function)
find_in_diary_tool = {
    "function_declarations": [
        {
            "name": "find_in_diary",
            "description": "This is a personal daily diary and use to get information about me and what I did in the "
                           "past, if no date or timeframe specified then search in the whole diary. Use this when any "
                           "query has me, my and I words. Dont say is there anything else I can help you with but "
                           "rather stay quite until next question asked",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "The query string to search the document index."
                    }
                },
                "required": ["query"]
            }
        }
    ]
}


@decorator_time_taken
def get_exchange_rate(currency_from, currency_to, currency_date):
    params = {"from": currency_from, "to": currency_to, "date": currency_date}
    url = f"https://api.frankfurter.app/{params['date']}"
    api_response = requests.get(url, params=params)
    return api_response.text


# Define the tool (function)
exchange_rate_tool = {
    "function_declarations": [
        {
            "name": "get_exchange_rate",
            "description": "Get the exchange rate for currencies between countries",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "currency_date": {
                        "type": "string",
                        "description": "A date that must always be in YYYY-MM-DD format or the value 'latest' if a "
                                       "time period is not specified"
                    },
                    "currency_from": {
                        "type": "string",
                        "description": "The currency to convert from in ISO 4217 format"
                    },
                    "currency_to": {
                        "type": "string",
                        "description": "The currency to convert to in ISO 4217 format"
                    }
                },
                "required": [
                    "currency_from",
                    "currency_date",
                ]
            }
        }
    ]
}
