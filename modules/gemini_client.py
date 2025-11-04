import google.generativeai as genai
import os

def ask_gemini_for_medicine(context: str, preferred_models=None) -> str:
    """
    Safe Gemini wrapper:
    - Reads GEMINI_API_KEY from environment.
    - Lists available models (for the key), picks a suitable one, and calls it.
    - Returns formatted text or an error string starting with 'Gemini API error:'.
    """
    api_key = os.getenv('GEMINI_API_KEY')  # fallback key
    if not api_key:
        return 'Gemini API error: Missing GEMINI_API_KEY environment variable.'

    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models()]

        if preferred_models is None:
            preferred_models = [
                "models/gemini-2.0-flash",
                "models/gemini-1.5-pro",
                "models/gemini-1.5-flash",
                "models/text-bison-001",
            ]

        chosen = next((pm for pm in preferred_models if pm in models), None)
        if not chosen:
            return f"Gemini API error: No compatible model found. Available: {models}"

        model = genai.GenerativeModel(chosen)

        prompt = f"""
You are a professional pharmacist AI.

Analyze the provided text or barcode and respond in the following clear format:

Branded Name: <branded name>
Generic: <generic>
Company: <company>
Price per tablet (approx): ₹<price>
Uses: <short one-line use>

If unknown, say only 'Unknown medicine'.

Context: {context}
"""

        resp = model.generate_content(prompt)

        # Safety checks
        if not hasattr(resp, "text") or not resp.text:
            return "Gemini API error: Empty response from model."

        text = resp.text.strip()

        # Avoid the model echoing back the prompt
        if "Branded Name" not in text and "Unknown" not in text:
            return "Unknown medicine"

        return text

    except Exception as e:
        return f"Gemini API error: {str(e)}"
print(ask_gemini_for_medicine("Barcode: 8901522000563, medicine label says 'Crocin Advance Paracetamol GSK'")
)
