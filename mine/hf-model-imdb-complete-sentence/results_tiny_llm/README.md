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

This model is a fine-tuned version of [](https://huggingface.co/) on an unknown dataset.

## Model description

More information needed

## Intended uses & limitations

More information needed

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
