import streamlit as st
import subprocess
import pandas as pd
import json
import os
import tempfile

# ---------------- CONFIG ----------------

WA_TXT_PATH = "_chat.txt"
WA_TRANSLATED_CSV = "whatsapp_translated.csv"
MAPPING_JSON = "character_user_mapping.json"

st.set_page_config(
    page_title="3 Idiots Character Mapper",
    layout="centered"
)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #e8f0fe;
    }

    .block-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        max-width: 900px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.title("🎬 3 Idiots × WhatsApp Character Mapper")

st.markdown("""
Upload a WhatsApp chat export (`.txt`).

Pipeline:
1. Parse WhatsApp chat  
2. Translate (if enabled)  
3. Embed users  
4. Match movie characters  
""")

# ---------------- UPLOAD ----------------

uploaded_file = st.file_uploader(
    "Upload WhatsApp chat (.txt)",
    type=["txt"]
)

if uploaded_file:
    # Save chat as expected filename
    with open(WA_TXT_PATH, "wb") as f:
        f.write(uploaded_file.read())

    st.success("Chat uploaded")

    # ---------------- PARSE + TRANSLATE ----------------

    st.subheader("1️⃣ Parsing & Translating Chat")

    with st.spinner("Running wa_parse.py..."):
        subprocess.run(
            ["python3", "wa_parse.py"],
            check=True
        )

    st.success("WhatsApp parsed & translated")

    if not os.path.exists(WA_TRANSLATED_CSV):
        st.error("whatsapp_translated.csv not found")
        st.stop()

    df = pd.read_csv(WA_TRANSLATED_CSV)
    st.write(f"Parsed **{len(df)} messages**")
    st.dataframe(df.head())

    # ---------------- EMBEDDING ----------------

    st.subheader("2️⃣ Embedding WhatsApp Users")

    with st.spinner("Running embed_wa.py..."):
        subprocess.run(
            ["python3", "embed_wa.py"],
            check=True
        )

    st.success("User embeddings generated")

    # ---------------- MATCHING ----------------

    st.subheader("3️⃣ Matching Characters")

    with st.spinner("Running similarity.py..."):
        subprocess.run(
            ["python3", "similarity.py"],
            check=True
        )

    if not os.path.exists(MAPPING_JSON):
        st.error("character_user_mapping.json not found")
        st.stop()

    with open(MAPPING_JSON) as f:
        mapping = json.load(f)

    result_df = pd.DataFrame(
        mapping.items(),
        columns=["Character", "Assigned User"]
    )

    st.dataframe(result_df)

    # ---------------- DOWNLOAD ----------------

    st.subheader("⬇️ Download Results")

    st.download_button(
        "Download JSON",
        json.dumps(mapping, indent=2),
        file_name="character_user_mapping.json",
        mime="application/json"
    )

    st.download_button(
        "Download CSV",
        result_df.to_csv(index=False),
        file_name="character_user_mapping.csv",
        mime="text/csv"
    )
