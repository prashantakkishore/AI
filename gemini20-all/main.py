# main.py
# pip install google-genai==0.3.0
import audioTranscribe as at
import asyncio
import base64
import json
import websockets
from google import genai
import chromavectordb as cvd
import Tools as tools
from ToolHandler import ToolHandler
import markdown
import re  # Import the regular expression module
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


# Load API key from environment
# os.environ['GOOGLE_API_KEY'] = ''
MODEL = "gemini-2.0-flash-exp"  # use your model ID
TRANSCRIPTION_MODEL = "gemini-1.5-flash-8b"
client = genai.Client(
    http_options={
        'api_version': 'v1alpha',
    }
)


def markdown_to_html(md_text):
    """Converts Markdown text to HTML, performing basic sanitization and syntax highlighting."""
    # Extensions for better Markdown support (e.g., tables, fenced code blocks)
    extensions = ['nl2br', 'fenced_code', 'tables', 'sane_lists', 'codehilite']
    extension_configs = {
        'codehilite': {
            'guess_lang': False,  # Disable language guessing; rely on explicit language tags
            'linenums': False,     # Disable line numbers (optional)
            'css_class': 'highlight'  # CSS class for the code block
        }
    }
    html = markdown.markdown(md_text, extensions=extensions, extension_configs=extension_configs, output_format="html5")  # Specify html5 for modern browsers

    # Basic sanitization using regular expressions (VERY LIMITED!)
    # Remove potentially dangerous attributes (e.g., onclick, onload)
    html = re.sub(r'<(.*?) (.*?)on[a-z]+=[\'"].*?[\'"](.*?)>', r'<\1 \3>', html, flags=re.IGNORECASE)
    # Remove javascript: URLs
    html = re.sub(r'href=[\'"]javascript:.*?[\'"]', 'href="#"', html, flags=re.IGNORECASE)

    return html


async def gemini_session_handler(client_websocket: websockets.ClientConnection):
    """Handles the interaction with Gemini API within a websocket session.

    Args:
        client_websocket: The websocket connection to the client.
    """
    try:
        config_message = await client_websocket.recv()
        config_data = json.loads(config_message)
        config = config_data.get("setup", {})

        available_tools = tools  # Access the tools module
        config["tools"] = [tools.write_to_diary_tool, tools.find_in_diary_tool, tools.exchange_rate_tool]

        tools_handler = ToolHandler(available_tools, client_websocket)


        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected to Gemini API")
            chat = client.chats.create(model=MODEL)

            async def send_to_gemini():
                """Sends messages from the client websocket to the Gemini API."""
                try:
                    async for message in client_websocket:
                        try:
                            data = json.loads(message)
                            if "realtime_input" in data:
                                for chunk in data["realtime_input"]["media_chunks"]:
                                    if "data" in chunk:
                                        if chunk["mime_type"] == "audio/pcm":
                                            await session.send(input={"mime_type": "audio/pcm", "data": chunk["data"]})
                                            # at.transcribe_vosk(chunk["data"])
                                        elif chunk["mime_type"] == "audio/transcribe":
                                            transcribed_text = at.call_gemini_transcribe(chunk["data"])
                                            await client_websocket.send(json.dumps({"transcribe_json": transcribed_text}))
                                        elif chunk["mime_type"] == "image/jpeg":
                                            await session.send(input={"mime_type": "image/jpeg", "data": chunk["data"]})

                                        elif chunk["mime_type"] == "application/json":

                                            response = chat.send_message_stream(chunk["data"])
                                            # cvd.update_embeddings_new_text(chunk["data"])
                                            for chat_response_chunk in response:
                                                html_text = markdown_to_html(chat_response_chunk.text)
                                                await client_websocket.send(json.dumps({"json": html_text}))

                        except Exception as client_closed:
                            print(f"Error sending to Gemini send_to_gemini: {client_closed}")
                    print("Client connection closed (send)")
                except Exception as client_closed:
                    print(f"Error sending to Gemini send_to_gemini connection: {client_closed}")
                finally:
                    print("send_to_gemini closed")

            async def receive_from_gemini():
                """Receives responses from the Gemini API and forwards them to the client, looping until turn is
                complete."""
                try:
                    while True:
                        try:
                            print("receiving from gemini")
                            await client_websocket.send(
                                json.dumps({"setupComplete": "true"}))

                            async for response in session.receive():
                                # first_response = True
                                # print(f"response: {response}")
                                if response.server_content is None:
                                    if response.tool_call is not None:
                                        # handle the tool call
                                        print(f"Tool call received: {response.tool_call}")

                                        function_calls = response.tool_call.function_calls
                                        function_responses = await tools_handler.process_tool_calls(function_calls)

                                        # Send function response back to Gemini
                                        print(f"function_responses: {function_responses}")
                                        await session.send(input=function_responses)
                                        continue

                                    # print(f'Unhandled server message! - {response}')
                                    # continue

                                model_turn = response.server_content.model_turn
                                if model_turn:
                                    for part in model_turn.parts:
                                        # print(f"part: {part}")
                                        if hasattr(part, 'text') and part.text is not None:
                                            # Convert Markdown to HTML and sanitize
                                            html_text = markdown_to_html(part.text)
                                            await client_websocket.send(json.dumps({"text": html_text}))
                                        elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                            # if first_response:
                                            # print("audio mime_type:", part.inline_data.mime_type)
                                            # first_response = False
                                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            await client_websocket.send(json.dumps({
                                                "audio": base64_audio,
                                            }))

                                if response.server_content.turn_complete:
                                    await client_websocket.send(json.dumps({
                                        "serverContent": {"turnComplete": True},
                                    }))
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