import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# ---------------- CONFIG ----------------

CSV_PATH = "whatsapp_translated.csv"
MODEL_NAME = "all-mpnet-base-v2"
OUT_DIR = "embeddings_wa"

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------- LOAD DATA ----------------

df = pd.read_csv(CSV_PATH)

assert "person" in df.columns
assert "text_en" in df.columns

# Optional: drop very short / empty messages
df = df[df["text_en"].str.len() > 5].reset_index(drop=True)

# ---------------- LOAD MODEL ----------------

model = SentenceTransformer(MODEL_NAME)

# ---------------- EMBED ALL MESSAGES ----------------

texts = df["text_en"].tolist()

print(f"Embedding {len(texts)} user messages...")

embeddings = model.encode(
    texts,
    show_progress_bar=True,
    batch_size=32
)

# ---------------- AGGREGATE PER USER ----------------

df["embedding_index"] = range(len(embeddings))

user_embeddings = {}

for person, group in df.groupby("person"):
    idxs = group["embedding_index"].values
    embs = embeddings[idxs]
    user_embeddings[person] = embs.mean(axis=0)

# ---------------- SAVE ----------------

np.save(
    f"{OUT_DIR}/user_embeddings.npy",
    user_embeddings,
    allow_pickle=True
)

print(f"Saved embeddings for {len(user_embeddings)} users")
print("USER EMBEDDING STEP COMPLETE")
