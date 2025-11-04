from .database import load_medicines
from .gemini_client import ask_gemini_for_medicine
from .llm_fallback_local import ask_local_llm

def chatbot_lookup(query: str):
    df = load_medicines()
    if not df.empty:
        if 'Branded_Name' in df.columns:
            found = df[df['Branded_Name'].str.contains(query, case=False, na=False, regex=False)]
            if not found.empty:
                row = found.iloc[0]
                text = format_row(row)
                return text, False
        if 'Generic_Name' in df.columns:
            found = df[df['Generic_Name'].str.contains(query, case=False, na=False, regex=False)]
            if not found.empty:
                row = found.iloc[0]
                text = format_row(row)
                return text, False
    context = f'User query: {query}'
    gem = ask_gemini_for_medicine(context)
    if gem.lower().startswith('gemini api error') or gem.lower().startswith('unknown'):
        local = ask_local_llm(context)
        return (local if local else gem), True
    return gem, True

def format_row(row):
    return (f"Branded Name: {row.get('Branded_Name','-')}\n"
            f"Generic: {row.get('Generic_Name','-')}\n"
            f"Company: {row.get('Company','-')}\n"
            f"Price per tablet (approx): ₹{row.get('Price','-')}\n"
            f"Uses: {row.get('Description','-')}")
