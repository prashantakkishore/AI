## Run the Flask server first
## python clients/flask_server_model.py
## Then run the curl client
curl -X POST http://127.0.0.1:5000/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "The best part about AI is"}'
