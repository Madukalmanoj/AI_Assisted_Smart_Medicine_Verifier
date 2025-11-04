import streamlit as st
from modules.barcode_scanner import verify_medicine_input
from modules.chatbot import chatbot_lookup
from modules.database import load_medicines, append_medicine
from modules.utils import parse_llm_response, is_llm_response
import tempfile, os
import time

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="💊 Smart Medicine Verifier", layout="wide")
st.title("💊 Smart Medicine Verifier — Gemini + Local AI + DB")

tabs = st.tabs(["🔍 Scanner", "💬 Chatbot", "🗂️ Database"])

# =====================================================
# 🔍 TAB 1 — SCANNER
# =====================================================
with tabs[0]:
    st.header("Scanner — Upload image or enter barcode/batch/name")
    uploaded_file = st.file_uploader(
        "Upload packaging image (png/jpg/jpeg)", type=["png", "jpg", "jpeg"]
    )
    manual_input = st.text_input("Or paste barcode / batch / product name:")
    analyze = st.button("Analyze")

    if analyze:
        if not uploaded_file and not manual_input.strip():
            st.warning("Please provide an image or text input.")
        else:
            tpath = None
            try:
                # Temporary save for uploaded image
                if uploaded_file:
                    tf = tempfile.NamedTemporaryFile(
                        delete=False, suffix="." + uploaded_file.name.split(".")[-1]
                    )
                    tf.write(uploaded_file.read())
                    tf.flush()
                    tpath = tf.name

                # Run verification
                res = verify_medicine_input(input_value=manual_input.strip(), image_path=tpath)
                st.markdown("---")
                st.subheader("🧾 Result:")

                if isinstance(res, dict) and "Branded_Name" in res:
                    st.success("✅ Medicine Details Found")
                    st.markdown(f"**🧾 Branded Name:** {res.get('Branded_Name', 'N/A')}")
                    st.markdown(f"**💊 Generic:** {res.get('Generic_Name', 'N/A')}")
                    st.markdown(f"**🏭 Company:** {res.get('Company', 'N/A')}")
                    st.markdown(f"**💰 Price:** ₹{res.get('Price', 'N/A')}")
                    st.markdown(f"**⚕️ Uses:** {res.get('Description', 'N/A')}")
                    st.caption(f"Source: {res.get('Source', 'Unknown')}")

                    if st.button("💾 Save to Database"):
                        try:
                            append_medicine(res)
                            st.success("✅ Saved to Database.")
                        except Exception as e:
                            st.error(f"Error saving: {e}")

                elif isinstance(res, dict) and "text" in res:
                    st.markdown(f"```markdown\n{res['text']}\n```")
                    st.caption(f"Source: {res.get('Source', 'Unknown')}")

                    if is_llm_response(res["text"]):
                        if st.button("💾 Accept & Save to DB"):
                            try:
                                row = parse_llm_response(res["text"])
                                append_medicine(row)
                                st.success("✅ Saved to Database.")
                            except Exception as e:
                                st.error(f"Error saving: {e}")

                elif isinstance(res, dict) and "error" in res:
                    st.error(res["error"])
                else:
                    st.info("ℹ️ No recognizable data found.")
                    st.code(str(res))

            except Exception as e:
                st.error(f"Processing error: {e}")

            finally:
                if tpath and os.path.exists(tpath):
                    try:
                        time.sleep(0.5)  # wait a moment for OCR or OpenCV to release it
                        os.remove(tpath)
                    except PermissionError:
                        print(f"⚠️ Could not delete temp file (in use): {tpath}")


# =====================================================
# 💬 TAB 2 — CHATBOT
# =====================================================
with tabs[1]:
    st.header("Chatbot Assistant")
    q = st.text_input("Ask about a medicine (brand/generic):")
    if st.button("Ask"):
        if not q.strip():
            st.warning("Enter a query.")
        else:
            ans, used_llm = chatbot_lookup(q.strip())
            st.markdown("**Answer:**")
            st.markdown(f"```markdown\n{ans}\n```")

            if used_llm and is_llm_response(ans):
                if st.button("💾 Accept LLM Result to DB"):
                    try:
                        row = parse_llm_response(ans)
                        append_medicine(row)
                        st.success("✅ Saved to Database.")
                    except Exception as e:
                        st.error(f"Error saving: {e}")

# =====================================================
# 🗂️ TAB 3 — DATABASE
# =====================================================
with tabs[2]:
    st.header("Local Database")
    df = load_medicines()
    st.dataframe(df, width='stretch')  # ✅ replaced use_container_width
    st.download_button(
        "⬇️ Download CSV", df.to_csv(index=False), file_name="medicines_export.csv"
    )
