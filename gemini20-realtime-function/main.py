## pip install google-genai==0.3.0

import asyncio
import json
import os
import websockets
from google import genai
import base64
import requests
import markdown
import re
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerativeModel,
    Part,
    Tool,
)

# Load API key from environment
# os.environ['GOOGLE_API_KEY'] = ''
MODEL = "gemini-2.0-flash-exp"  # use your model ID

client = genai.Client(
    http_options={
        'api_version': 'v1alpha',
    }
)


def get_exchange_rate(currency_from, currency_to, currency_date):
    params = {"from": currency_from, "to": currency_to, "date": currency_date}
    url = f"https://api.frankfurter.app/{params['date']}"
    api_response = requests.get(url, params=params)
    return api_response.text


# Define the tool (function)
get_exchange_rate_func = {
    "function_declarations": [
        {
            "name": "get_exchange_rate",
            "description": "Get the exchange rate for currencies between countries",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "currency_date": {
                        "type": "string",
                        "description": "A date that must always be in YYYY-MM-DD format or the value 'latest' if a time period is not specified"
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


# Mock function for set_light_values
def set_light_values(brightness, color_temp):
    return {
        "brightness": brightness,
        "colorTemperature": color_temp,
    }


# Define the tool (function)
tool_set_light_values = {
    "function_declarations": [
        {
            "name": "set_light_values",
            "description": "Set the brightness and color temperature of a room light.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "brightness": {
                        "type": "NUMBER",
                        "description": "Light level from 0 to 100. Zero is off and 100 is full brightness"
                    },
                    "color_temp": {
                        "type": "STRING",
                        "description": "Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`."
                    }
                },
                "required": ["brightness", "color_temp"]
            }
        }
    ]
}


async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
    """Handles the interaction with Gemini API within a websocket session.

    Args:
        client_websocket: The websocket connection to the client.
    """
    try:
        config_message = await client_websocket.recv()
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})

        config["tools"] = [tool_set_light_values, get_exchange_rate_func]

        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini API")
            chat = client.chats.create(model="gemini-2.0-flash")
            async def send_to_gemini():
                """Sends messages from the client websocket to the Gemini API."""
                try:
                    async for message in client_websocket:
                        try:
                            data = json.loads(message)
                            if "realtime_input" in data:
                                for chunk in data["realtime_input"]["media_chunks"]:
                                    if chunk["mime_type"] == "audio/pcm":
                                        await session.send(input={"mime_type": "audio/pcm", "data": chunk["data"]})

                                    elif chunk["mime_type"] == "image/jpeg":
                                        await session.send(input={"mime_type": "image/jpeg", "data": chunk["data"]})

                                    elif chunk["mime_type"] == "application/json":


                                        response = chat.send_message_stream(chunk["data"])
                                        for chunk in response:
                                            html_content = markdown.markdown(chunk.text)
                                            html_content = re.sub(r"^<p>", " ", html_content)
                                            html_content = re.sub(r"</p>$", " ", html_content)
                                            await client_websocket.send(json.dumps({"json": html_content}))



                        except Exception as e:
                            print(f"Error sending to Gemini send_to_gemini: {e}")
                    print("Client connection closed (send)")
                except Exception as e:
                    print(f"Error sending to Gemini send_to_gemini connection: {e}")
                finally:
                    print("send_to_gemini closed")

            async def receive_from_gemini():
                """Receives responses from the Gemini API and forwards them to the client, looping until turn is complete."""
                try:
                    while True:
                        try:
                            print("receiving from gemini")
                            async for response in session.receive():
                                #first_response = True
                                #print(f"response: {response}")
                                if response.server_content is None:
                                    if response.tool_call is not None:
                                        #handle the tool call
                                        print(f"Tool call received: {response.tool_call}")

                                        function_calls = response.tool_call.function_calls
                                        function_responses = []

                                        for function_call in function_calls:
                                            name = function_call.name
                                            args = function_call.args
                                            # Extract the numeric part from Gemini's function call ID
                                            call_id = function_call.id

                                            # Validate function name
                                            if name == "set_light_values":
                                                try:
                                                    result = set_light_values(int(args["brightness"]),
                                                                              args["color_temp"])
                                                    function_responses.append(
                                                        {
                                                            "name": name,
                                                            #"response": {"result": "The light is broken."},
                                                            "response": {"result": result},
                                                            "id": call_id
                                                        }
                                                    )
                                                    await client_websocket.send(
                                                        json.dumps({"text": json.dumps(function_responses)}))
                                                    print("Function executed")
                                                except Exception as e:
                                                    print(f"Error executing function: {e}")
                                                    continue
                                            # Validate function name
                                            if name == "get_exchange_rate":
                                                try:
                                                    result = get_exchange_rate(args["currency_from"],
                                                                               args["currency_to"],
                                                                               args["currency_date"])
                                                    function_responses.append(
                                                        {
                                                            "name": name,
                                                            #"response": {"result": "The light is broken."},
                                                            "response": {"result": result},
                                                            "id": call_id
                                                        }
                                                    )
                                                    await client_websocket.send(
                                                        json.dumps({"text": json.dumps(function_responses)}))
                                                    print("Function executed")
                                                except Exception as e:
                                                    print(f"Error executing function: {e}")
                                                    continue

                                        # Send function response back to Gemini
                                        print(f"function_responses: {function_responses}")
                                        await session.send(input=function_responses)
                                        continue

                                    #print(f'Unhandled server message! - {response}')
                                    #continue

                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    for part in model_turn.parts:
                                        #print(f"part: {part}")
                                        if hasattr(part, 'text') and part.text is not None:
                                            #print(f"text: {part.text}")
                                            await client_websocket.send(json.dumps({"text": part.text}))
                                        elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                            # if first_response:
                                            #print("audio mime_type:", part.inline_data.mime_type)
                                            #first_response = False
                                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            await client_websocket.send(json.dumps({
                                                "audio": base64_audio,
                                            }))
                                            print("audio received")

                                if response.server_content.turn_complete:
                                    print('\n<Turn complete>')
                        except websockets.exceptions.ConnectionClosedOK:
                            print("Client connection closed normally (receive)")
                            break  # Exit the loop if the connection is closed
                        except Exception as e:
                            print(f"Error receiving from Gemini: {e}")
                            break  # exit the lo

                except Exception as e:
                    print(f"Error receiving from Gemini: {e}")
                finally:
                    print("Gemini connection closed (receive)")

            # Start send loop
            send_task = asyncio.create_task(send_to_gemini())
            # Launch receive loop as a background task
            receive_task = asyncio.create_task(receive_from_gemini())
            await asyncio.gather(send_task, receive_task)


    except Exception as e:
        print(f"Error in Gemini session: {e}")
    finally:
        print("Gemini session closed.")


async def main() -> None:
    async with websockets.serve(gemini_session_handler, "localhost", 9082):
        print("Running websocket server localhost:9082...")
        await asyncio.Future()  # Keep the server running indefinitely


if __name__ == "__main__":
    asyncio.run(main())
