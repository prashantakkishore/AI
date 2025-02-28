import requests
import chromavectordb as cvd
from decorators import decorator_time_taken

# Constants for API URLs (consider moving to config file)
FRANKFURTER_API_URL = "https://api.frankfurter.app/{date}"


class Tools:
    """
    A class containing various tools, including diary management and external API access.
    """

    def __init__(self):
        """Initializes the Tools class. Potentially initializes ChromaDB here."""
        pass  # Placeholder for ChromaDB initialization if needed

    @decorator_time_taken
    def write_to_diary(self, notes: str) -> str:
        """Writes notes to the diary using Chroma Vector DB."""
        cvd.update_embeddings_new_text(notes)
        return "Saved to diary"

    @decorator_time_taken
    def find_in_diary(self, date: str, query: str) -> str:
        """Finds information in the diary using Chroma Vector DB based on a date and query."""
        return cvd.generate_answer_user(date, query=query)

    @decorator_time_taken
    def get_exchange_rate(self, currency_from: str, currency_to: str, currency_date: str) -> str:
        """Retrieves the exchange rate between two currencies from the Frankfurter API."""
        params = {"from": currency_from, "to": currency_to, "date": currency_date}
        url = FRANKFURTER_API_URL.format(date=params["date"])
        try:
            api_response = requests.get(url, params=params)
            api_response.raise_for_status()  # Raise HTTPError for bad responses
            return api_response.text
        except requests.exceptions.RequestException as e:
            return f"Error fetching exchange rate: {e}"


# Define the tool (function) definitions outside the class
write_to_diary_tool = {
    "function_declarations": [
        {
            "name": "write_to_diary",
            "description": "Write notes to the personal daily diary or take notes.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "notes": {
                        "type": "STRING",
                        "description": "The notes to write to the diary.",
                    }
                },
                "required": ["notes"],
            },
        }
    ]
}


find_in_diary_tool = {
    "function_declarations": [
        {
            "name": "find_in_diary",
            "description": (
                "Search the personal daily diary for past information.  If no date is specified, search the entire diary. "
                "Convert 'yesterday' or 'today' to the exact date.  Use this tool when the query contains 'me', 'my', or 'I'. "
                "Do not offer further assistance after providing the answer."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "The query string to search the diary.",
                    },
                    "date": {
                        "type": "STRING",
                        "description": "The date to search for (YYYY-MM-DD).",
                    },
                },
                "required": ["query"],
            },
        }
    ]
}


exchange_rate_tool = {
    "function_declarations": [
        {
            "name": "get_exchange_rate",
            "description": "Get the exchange rate between two currencies.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "currency_date": {
                        "type": "string",
                        "description": "The date for the exchange rate (YYYY-MM-DD) or 'latest'.",
                    },
                    "currency_from": {
                        "type": "string",
                        "description": "The currency to convert from (ISO 4217).",
                    },
                    "currency_to": {
                        "type": "string",
                        "description": "The currency to convert to (ISO 4217).",
                    },
                },
                "required": ["currency_from", "currency_date"],
            },
        }
    ]
}


if __name__ == '__main__':
    # Example Usage
    tools = Tools()

    diary_result = tools.write_to_diary("Today I went for a walk and saw a cute dog.")
    print(f"Diary Result: {diary_result}")

    search_result = tools.find_in_diary(date="latest", query="walk")
    print(f"Search Result: {search_result}")

    exchange_rate_result = tools.get_exchange_rate(
        currency_from="USD", currency_to="EUR", currency_date="latest"
    )
    print(f"Exchange Rate Result: {exchange_rate_result}")