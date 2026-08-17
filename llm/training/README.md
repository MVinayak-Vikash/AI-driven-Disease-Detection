# 🧠 LLM Fine-Tuning with Unsloth

This directory provides scripts to fine-tune open-source instruct models (such as **Meta-Llama-3-8B-Instruct** or **Mistral-7B-Instruct**) for specialized clinical screening and decision-support reasoning using **Unsloth**.

---

## 🎯 Fine-Tuning Objectives
1. **Multi-Modal Synthesis**: Teach the LLM to integrate patient age, biological sex, comorbidities, and reported symptoms with sensor metrics (BPM, HRV/RMSSD, rhythm irregularity index).
2. **Baseline Deviation Reasoning**: Enable the model to recognize and weight shifts relative to the patient's own historical baseline rather than applying static population thresholds.
3. **Structured Clinical JSON Compliance**: Guarantee 100% adherence to the required JSON schema output with zero hallucinations or conversational filler.
4. **Clinical Safety & Uncertainty**: Enforce explicit confidence reporting and proper triage escalation to medical specialists without claiming definitive diagnostic finality.

---

## 🚀 How to Run on Google Colab or Local GPU (16GB VRAM)

### 1. Install Dependencies
```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes
```

### 2. Generate Dataset
```bash
python ../datasets/generate_dataset.py
```

### 3. Start Training
```bash
python train_unsloth.py \
    --model_name "unsloth/llama-3-8b-Instruct-bnb-4bit" \
    --dataset "../datasets/sample_training_dataset.jsonl" \
    --output_dir "../checkpoints/cardionav-unsloth-lora" \
    --epochs 3
```

---

## 🔄 Using in the FastAPI Runtime

Set in your `.env`:
```env
AI_PROVIDER=finetuned
UNSLOTH_MODEL_PATH=./llm/checkpoints/cardionav-unsloth-lora
```

When started, FastAPI will load the LoRA weights and perform high-speed local inference. If no GPU is present, setting `AI_PROVIDER=mock` provides an identical response contract with zero external dependencies.
