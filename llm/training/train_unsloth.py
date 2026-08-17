"""
Unsloth Fine-Tuning Script for CardioNav AI Clinical Decision Support.

Fine-tunes open-weight instruct models (Llama-3-8B-Instruct, Mistral-7B-Instruct, Qwen-2.5-7B)
on multi-modal clinical reasoning, baseline delta sensitivity, and strict JSON output.

Usage:
    python train_unsloth.py --model_name "unsloth/llama-3-8b-Instruct-bnb-4bit" --dataset "../datasets/sample_training_dataset.jsonl"
"""

import os
import argparse
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

def train(
    model_name: str = "unsloth/llama-3-8b-Instruct-bnb-4bit",
    dataset_path: str = "../datasets/sample_training_dataset.jsonl",
    output_dir: str = "../checkpoints/cardionav-unsloth-lora",
    max_seq_length: int = 2048,
    epochs: int = 3,
    batch_size: int = 2,
    learning_rate: float = 2e-4
):
    try:
        from unsloth import FastLanguageModel, is_bfloat16_supported
    except ImportError:
        print("Unsloth is not installed. To train, run in an environment with: pip install unsloth")
        return

    print(f"Loading base model: {model_name}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True
    )

    print("Configuring LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42
    )

    print(f"Loading dataset from {dataset_path}...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
        return {"text": texts}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    print("Starting SFT Trainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            warmup_steps=10,
            num_train_epochs=epochs,
            learning_rate=learning_rate,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            output_dir=output_dir,
            save_strategy="epoch"
        )
    )

    trainer.train()

    print(f"Saving fine-tuned LoRA checkpoint to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("Fine-tuning completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="unsloth/llama-3-8b-Instruct-bnb-4bit")
    parser.add_argument("--dataset", type=str, default="../datasets/sample_training_dataset.jsonl")
    parser.add_argument("--output_dir", type=str, default="../checkpoints/cardionav-unsloth-lora")
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    train(
        model_name=args.model_name,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        epochs=args.epochs
    )
