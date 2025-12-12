import torch
from datasets import load_dataset
from transformers import GPT2Config, AutoModelForCausalLM, Trainer, TrainingArguments, AutoTokenizer, DataCollatorForLanguageModeling
import math
from multiprocessing import freeze_support
import os

# Define where the model will be saved
OUTPUT_NAME = "results_tiny_llm"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), OUTPUT_NAME)

def train():
    # Add freeze_support() for multiprocessing compatibility on Windows
    freeze_support()
    print(f"Initializing tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("gpt2", use_fast=True)
    
    # --- 1. Define the Small Model Configuration ---
    GPT2_VOCAB_SIZE = tokenizer.vocab_size 

    config = GPT2Config(
        vocab_size=GPT2_VOCAB_SIZE,
        n_positions=128,
        n_embd=64,
        n_layer=4,
        n_head=4,
        bos_token_id=tokenizer.bos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    model = AutoModelForCausalLM.from_config(config)
    total_params = model.num_parameters() / 1_000_000
    print(f"Initialized model with {total_params:.2f}M parameters.")

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"Tokenizer vocabulary size: {tokenizer.vocab_size}")

    # --- 2. Load and Preprocess a Small Dataset ---
    dataset = load_dataset("imdb", split="train[:1000]")

    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, max_length=config.n_positions, padding="max_length")

    tokenized_datasets = dataset.map(
        tokenize_function,
        batched=True,
        num_proc=4,
        remove_columns=["text"],
    )

    # --- 3. Define Training Arguments and Trainer ---
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        overwrite_output_dir=True,
        per_device_train_batch_size=16,
        num_train_epochs=1,
        save_steps=10_000,
        logging_steps=100,
        learning_rate=2e-4,
        push_to_hub=False, # Change this from False to True
        hub_model_id="prashantak/IMDB-Complete-Sentence-4M"
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=tokenized_datasets,
    )

    # --- 4. Train and Save ---
    print("Starting training...")
    trainer.train()
    print("Training finished.")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")

if __name__ == '__main__':
    train()
