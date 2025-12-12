from flask import Flask, request, jsonify
from transformers import pipeline
import os

app = Flask(__name__)

MODEL_NAME = "../results_tiny_llm"
MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_NAME)
# Load the model globally when the server starts
try:
    generator = pipeline("text-generation", model=MODEL_PATH, tokenizer=MODEL_PATH)
    print("Flask API: Model loaded successfully.")
except Exception as e:
    print(f"Flask API Error: {e}")
    generator = None

@app.route('/generate', methods=['POST'])
def generate():
    if generator is None:
        return jsonify({"error": "Model not loaded"}), 503
    
    # Get prompt from the incoming JSON request
    data = request.get_json(force=True)
    prompt = data.get("prompt", "")
    max_length = data.get("max_length", 50)

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    # Generate text
    result = generator(
        prompt, 
        max_new_tokens=max_length, 
        num_return_sequences=1, 
        truncation=True
    )
    
    generated_text = result[0]['generated_text']
    
    return jsonify({"prompt": prompt, "generated_text": generated_text})

if __name__ == '__main__':
    # Run the Flask app on localhost port 5000
    app.run(debug=True, port=5000)
