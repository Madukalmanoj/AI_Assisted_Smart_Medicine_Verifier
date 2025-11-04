from transformers import pipeline
import torch
import os

MODEL_NAME = os.getenv('LOCAL_LLM_MODEL', 'google/flan-t5-small')
_gen = None

def _load_local():
    global _gen
    if _gen is None:
        device = 0 if torch.cuda.is_available() else -1
        _gen = pipeline('text2text-generation', model=MODEL_NAME, tokenizer=MODEL_NAME, device=device)
    return _gen

def ask_local_llm(context: str) -> str:
    try:
        gen = _load_local()
        prompt = (f"You are an expert pharmacist. Context: {context}\n\n"
                  "Respond in plain text:\nBranded Name: <name>\nGeneric: <generic>\nCompany: <company>\n"
                  "Price per tablet (approx): ₹<number>\nUses: <one-line uses>\n\nIf unknown, reply 'Unknown medicine'.")
        out = gen(prompt, max_new_tokens=120, do_sample=False)
        return out[0].get('generated_text','').strip() if out else 'Unknown'
    except Exception as e:
        return f'LLM local error: {e}'
