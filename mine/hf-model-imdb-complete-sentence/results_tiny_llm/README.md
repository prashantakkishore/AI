---
library_name: transformers
tags:
- generated_from_trainer
model-index:
- name: IMDB-Complete-Sentence-4M
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# IMDB-Complete-Sentence-4M

This model is a fine-tuned version of [](https://huggingface.co/) on an small imdb dataset.
Check its HF space to try it out [](https://huggingface.co/spaces/prashantak/hf-space-imdb-complete-sentence)

## Model description

Very small 4m param model, created to see indepth of an LLM in an very small footprint

## Intended uses & limitations

As its so small models grammer could be wrong :)

--- Running Inference ---
- Prompt: This movie was
- Generated text: This movie was more get and, girl annoying out get the. been no.. I too, often hours this talent story anything 
never could this He the been mostbr said annoyinges He most don friend I never than often bet the budget her the from get I

--- Running Inference ---
- Prompt: The main character felt
- Generated text: The main character felt this three ( He no morees been than never I know said. film is hours hours good a more is. 
don don and < girl to too For dones is the than this a particularly film we this no many and never anything of house from

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 0.0002
- train_batch_size: 16
- eval_batch_size: 8
- seed: 42
- optimizer: Use OptimizerNames.ADAMW_TORCH_FUSED with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: linear
- num_epochs: 1

### Training results



### Framework versions

- Transformers 4.57.3
- Pytorch 2.9.1+cpu
- Datasets 3.6.0
- Tokenizers 0.22.1
