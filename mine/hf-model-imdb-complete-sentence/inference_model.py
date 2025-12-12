from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import os

# Define where the model was saved
MODEL_NAME = "results_tiny_llm"
MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_NAME)

def generate_text(prompt_text):
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model directory '{MODEL_PATH}' not found.")
        print("Please run 'train_model.py' first to create the model files.")
        return

    # print(f"Loading model and tokenizer from {MODEL_PATH}...")
    
    # We don't need AutoModelForCausalLM explicitly; the pipeline handles it
    generator = pipeline("text-generation", model=MODEL_PATH, tokenizer=MODEL_PATH)
    
    print("\n--- Running Inference ---")
    print(f"Prompt: {prompt_text}")

    # Generate text using the pipeline
    result = generator(prompt_text, max_new_tokens=50, num_return_sequences=1, truncation=True)
    
    print(f"Generated text: {result[0]['generated_text']}")

if __name__ == '__main__':
    prompt = "This movie was"
    generate_text(prompt)
    
    prompt_two = "The main character felt"
    generate_text(prompt_two)
