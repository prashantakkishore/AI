# tools_handler.py
import json
import Tools as tool


class ToolHandler:
    """Handles tool calls from the Gemini API and returns responses."""
    tools = tool

    def __init__(self, tools, client_websocket):
        """Initializes the ToolsHandler with the available tools and websocket client."""
        self.tools = tools
        self.client_websocket = client_websocket
        self.tool_functions = {
            "find_in_diary": self.execute_find_in_diary,
            "write_to_diary": self.execute_write_to_diary,
            "get_exchange_rate": self.execute_get_exchange_rate,
        }

    async def process_tool_calls(self, function_calls):
        """Processes a list of tool calls, executes them, and returns the responses.

        Args:
            function_calls: A list of function call objects from the Gemini API.

        Returns:
            A list of function response dictionaries to be sent back to the Gemini API.
        """
        function_responses = []
        for function_call in function_calls:
            name = function_call.name
            args = function_call.args
            call_id = function_call.id

            if name in self.tool_functions:
                try:
                    result = await self.tool_functions[name](args)
                    function_response = {
                        "name": name,
                        "response": {"result": result},
                        "id": call_id
                    }
                    function_responses.append(function_response)
                    await self.client_websocket.send(json.dumps({"text": json.dumps([function_response])}))
                    print(f"{name} function executed")
                except Exception as e:
                    print(f"Error executing function {name}: {e}")
            else:
                print(f"Unknown function call: {name}")

        return function_responses

    async def execute_find_in_diary(self, args):
        """Executes the 'find_in_diary' tool function.

        Args:
            args: A dictionary of arguments for the function.

        Returns:
            The result of the 'find_in_diary' function.
        """
        date = "ALL"
        if "date" in args:
            date = args["date"]
        query = args["query"]  # Ensure 'query' is always present

        if not query:
            raise ValueError("Query cannot be empty for find_in_diary tool")

        return self.tools.find_in_diary(date, query)

    async def execute_write_to_diary(self, args):
        """Executes the 'write_to_diary' tool function.

        Args:
            args: A dictionary of arguments for the function.

        Returns:
            The result of the 'write_to_diary' function.
        """
        notes = args["notes"]  # Ensure 'notes' is always present
        if not notes:
            raise ValueError("Notes cannot be empty for write_to_diary tool")
        return self.tools.write_to_diary(notes)

    async def execute_get_exchange_rate(self, args):
        """Executes the 'get_exchange_rate' tool function.

        Args:
            args: A dictionary of arguments for the function.

        Returns:
            The result of the 'get_exchange_rate' function.
        """

        currency_from = args["currency_from"]
        currency_to = args["currency_to"]
        currency_date = args["currency_date"]

        if not currency_from or not currency_to:
            raise ValueError("Currency from and to cannot be empty for get_exchange_rate tool")

        return self.tools.get_exchange_rate(currency_from, currency_to, currency_date)
