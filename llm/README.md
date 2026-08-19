# Unsloth integration

Fine-tuning is an offline workflow and must never run in FastAPI handlers. Place curated JSONL examples in `datasets/`, training scripts in `training/`, and exported adapter/model artifacts in `inference/` (ignored if large).

Set `AI_PROVIDER=finetuned`, `MODEL_NAME`, and (where applicable) `MODEL_BASE_URL` after exporting an Unsloth-compatible instruct model. `FineTunedLLMService` intentionally falls back to the safe validated contract until a runtime loader is added. `AI_PROVIDER=mock` remains the default for demos without a GPU.
