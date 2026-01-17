from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
import os

# ---------------- CONFIG ----------------

CSV_PATH = "parsed_script.csv"
MODEL_NAME = "all-mpnet-base-v2"
OUT_DIR = "embeddings"

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------- LOAD DATA ----------------

df = pd.read_csv(CSV_PATH)

assert "block_type" in df.columns
assert "text" in df.columns
assert "character" in df.columns

# ---------------- LOAD MODEL ----------------

model = SentenceTransformer(MODEL_NAME)

# ---------------- EMBED DIALOGUES ONLY ----------------
# (Narratives can be added later if you want)

dialogue_df = df[df["block_type"] == "DIALOGUE"].reset_index(drop=True)
texts = dialogue_df["text"].tolist()

print(f"Embedding {len(texts)} dialogue lines...")
embeddings = model.encode(
    texts,
    show_progress_bar=True,
    batch_size=32
)

# ---------------- SAVE DIALOGUE EMBEDDINGS ----------------

np.save(
    f"{OUT_DIR}/dialogue_embeddings.npy",
    embeddings
)

dialogue_df["embedding_index"] = range(len(embeddings))
dialogue_df.to_csv(
    f"{OUT_DIR}/dialogue_index.csv",
    index=False
)

# ---------------- BUILD CHARACTER EMBEDDINGS ----------------

character_embeddings = {}

for character, group in dialogue_df.groupby("character"):
    idxs = group["embedding_index"].values
    embs = embeddings[idxs]
    character_embeddings[character] = embs.mean(axis=0)

np.save(
    f"{OUT_DIR}/character_embeddings.npy",
    character_embeddings,
    allow_pickle=True
)

print(f"Saved {len(character_embeddings)} character embeddings")

# ---------------- TONE STATISTICS ----------------

tone_stats = (
    dialogue_df
    .groupby(["character", "explicit_tone"])
    .size()
    .unstack(fill_value=0)
)

tone_stats.to_csv(f"{OUT_DIR}/tone_stats.csv")

print("Saved tone statistics")

print("STEP 2 COMPLETE")
