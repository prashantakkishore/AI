import gradio as gr
from transformers import pipeline
import os

# Define where your model is saved locally
# Or change this to your Hugging Face model repository ID: 
MODEL_NAME = "../results_tiny_llm"
MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_NAME)

# Load the model and tokenizer using the transformers pipeline
try:
    print(f"Attempting to load model from: {MODEL_PATH}")
    # The pipeline will load the model configuration, weights, and tokenizer files
    generator = pipeline("text-generation", model=MODEL_PATH, tokenizer=MODEL_PATH)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Please ensure you have run train_model.py first and that the directory/files exist.")
    generator = None

def generate_text_web(prompt):
    """
    Generates text using the loaded LLM via the Gradio interface.
    """
    if generator is None:
        return "Model not loaded. Please train the model first or check console logs."
    
    # Generate text
    result = generator(
        prompt, 
        max_new_tokens=100, 
        num_return_sequences=1, 
        truncation=True
    )
    # The pipeline returns a list of dictionaries; we extract the generated text
    return result[0]['generated_text']

# Create the Gradio web interface
# This interface is defined even if the generator failed to load, 
# but the function it calls handles the error state gracefully.
interface = gr.Interface(
    fn=generate_text_web,
    inputs=gr.Textbox(lines=5, label="Enter your text prompt here"),
    outputs=gr.Textbox(lines=5),
    title="Tiny LLM Text Generator (From Scratch)",
    description="A minimal language model trained on a small IMDB dataset."
)

if __name__ == "__main__":
    # Launch the interface locally
    # share=True generates a temporary public link
    interface.launch(share=True)
