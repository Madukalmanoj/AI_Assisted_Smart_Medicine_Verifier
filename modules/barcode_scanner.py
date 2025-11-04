import cv2
from pyzbar.pyzbar import decode
import easyocr
from rapidfuzz import fuzz
import google.generativeai as genai
import os
from modules.llm_fallback_local import ask_local_llm
from modules.database import load_medicines


def scan_barcode_image(image_path):
    """Extract barcode text from image."""
    img = cv2.imread(image_path)
    if img is None:
        return None
    barcodes = decode(img)
    if barcodes:
        return barcodes[0].data.decode("utf-8")
    return None


def extract_text_ocr(image_path):
    """Extract text using OCR."""
    reader = easyocr.Reader(["en"])
    results = reader.readtext(image_path)
    return " ".join([res[1] for res in results])


def verify_medicine_input(input_value="", image_path=None):
    """
    Identify medicine using:
      1️⃣ Barcode
      2️⃣ OCR (if no barcode)
      3️⃣ Local DB match
      4️⃣ Gemini or Local LLM fallback
    """
    df = load_medicines()
    detected_text = ""

    if image_path:
        barcode = scan_barcode_image(image_path)
        if barcode:
            detected_text = barcode
        else:
            detected_text = extract_text_ocr(image_path)

    query = input_value or detected_text
    if not query:
        return {"error": "No valid input or barcode found."}

    # ---------- Step 2: Search local database ----------
    match = None
    if not df.empty:
        for _, row in df.iterrows():
            try:
                if (
                    fuzz.partial_ratio(query.lower(), str(row["Branded_Name"]).lower()) > 85
                    or fuzz.partial_ratio(query.lower(), str(row["Generic_Name"]).lower()) > 85
                    or fuzz.partial_ratio(query.lower(), str(row["Barcode"]).lower()) > 85
                ):
                    match = row
                    break
            except KeyError:
                continue

    if match is not None:
        text = (
            f"Branded Name: {match['Branded_Name']}\n"
            f"Generic: {match['Generic_Name']}\n"
            f"Company: {match['Company']}\n"
            f"Price per tablet (approx): ₹{match['Price']}\n"
            f"Uses: {match['Description']}\n"
        )
        return {
            "text": text,
            "Branded_Name": match["Branded_Name"],
            "Generic_Name": match["Generic_Name"],
            "Company": match["Company"],
            "Price": match["Price"],
            "Description": match["Description"],
            "Source": "Database"
        }

    # ---------- Step 3: Use Gemini / Local LLM ----------
    try:
        api_key = "AIzaSyCBrSn46GVynMxTMX_iG_1M0qPibOzFHy0"
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment variables")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = (
            f"Provide structured info about '{query}' in this format:\n"
            "Branded Name: <name>\nGeneric: <generic>\nCompany: <company>\n"
            "Price per tablet (approx): ₹<number>\nUses: <one-line uses>"
        )
        response = model.generate_content(prompt)
        text = response.text.strip()

        if not text or "Branded Name" not in text:
            text = ask_local_llm(query)

        lines = [l.strip() for l in text.split("\n") if ":" in l]
        data = {l.split(":")[0].strip(): l.split(":")[1].strip() for l in lines}

        return {
            "text": text,
            "Branded_Name": data.get("Branded Name", "Unknown"),
            "Generic_Name": data.get("Generic", ""),
            "Company": data.get("Company", ""),
            "Price": data.get("Price per tablet (approx)", "").replace("₹", "").strip(),
            "Description": data.get("Uses", ""),
            "Source": "Gemini"
        }

    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        text = ask_local_llm(query)
        lines = [l.strip() for l in text.split("\n") if ":" in l]
        data = {l.split(":")[0].strip(): l.split(":")[1].strip() for l in lines}
        return {
            "text": text,
            "Branded_Name": data.get("Branded Name", "Unknown"),
            "Generic_Name": data.get("Generic", ""),
            "Company": data.get("Company", ""),
            "Price": data.get("Price per tablet (approx)", "").replace("₹", "").strip(),
            "Description": data.get("Uses", ""),
            "Source": "Local LLM"
        }
