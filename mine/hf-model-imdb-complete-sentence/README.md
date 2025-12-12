## bash
* pip install huggingface_hub
* huggingface-cli login

## python
In your training script's TrainingArguments:
```
training_args = TrainingArguments(
    # ... other arguments
    push_to_hub=True, # Change this from False to True
    hub_model_id="YOUR_HF_USERNAME/prashantak-tiny-llm", # Name your model repo
)
```
You can also manually push after saving the model using the trainer object:
```
trainer.push_to_hub()
```