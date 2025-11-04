import pandas as pd
from pathlib import Path
from typing import Dict

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "medicines.csv"

def load_medicines() -> pd.DataFrame:
    try:
        if not DATA_PATH.exists():
            cols = ['Branded_Name','Generic_Name','Company','Price','Description','Batch','Barcode','Barcodes']
            return pd.DataFrame(columns=cols)
        df = pd.read_csv(DATA_PATH, dtype=str).fillna('')
        df.columns = [c.strip() for c in df.columns]
        for c in ['Branded_Name','Generic_Name','Company','Price','Description','Batch','Barcode','Barcodes']:
            if c not in df.columns:
                df[c] = ''
        return df
    except Exception as e:
        print(f"Database error: {e}")
        cols = ['Branded_Name','Generic_Name','Company','Price','Description','Batch','Barcode','Barcodes']
        return pd.DataFrame(columns=cols)

def append_medicine(row: Dict) -> None:
    df = load_medicines()
    for c in ['Branded_Name','Generic_Name','Company','Price','Description','Batch','Barcode','Barcodes']:
        row.setdefault(c, '')
    new_row = pd.DataFrame([row])
    df = pd.concat([df, new_row], ignore_index=True)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
