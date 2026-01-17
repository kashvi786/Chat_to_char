import numpy as np
import pandas as pd
import json
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import linear_sum_assignment


SCRIPT_CSV = "parsed_script.csv"
CHAR_EMB_PATH = "embeddings/character_embeddings.npy"
USER_EMB_PATH = "embeddings_wa/user_embeddings.npy"
OUT_PATH = "character_user_mapping.json"

script_df = pd.read_csv(SCRIPT_CSV)

dialogue_counts = (
    script_df[script_df["block_type"] == "DIALOGUE"]
    .groupby("character")
    .size()
    .sort_values(ascending=False)
)


char_embs = np.load(CHAR_EMB_PATH, allow_pickle=True).item()
user_embs = np.load(USER_EMB_PATH, allow_pickle=True).item()

users = list(user_embs.keys())
num_users = len(users)

K = max(3, num_users)

top_characters = [
    c for c in dialogue_counts.index
    if c in char_embs
][:K]

print(f"Using top {len(top_characters)} characters for matching")


characters = top_characters

char_matrix = np.vstack([char_embs[c] for c in characters])
user_matrix = np.vstack([user_embs[u] for u in users])

similarity = cosine_similarity(char_matrix, user_matrix)


cost = -similarity
row_ind, col_ind = linear_sum_assignment(cost)

matches = {
    characters[i]: users[j]
    for i, j in zip(row_ind, col_ind)
}


with open(OUT_PATH, "w") as f:
    json.dump(matches, f, indent=2)

print("\nOPTIMAL MATCHING RESULT:")
for c, u in matches.items():
    print(f"{c:20s} → {u}")

print("\nMATCH SCORES:")
for c, u in matches.items():
    i = characters.index(c)
    j = users.index(u)
    print(f"{c:20s} → {u:20s} : {similarity[i, j]:.3f}")

print(f"\nSaved {OUT_PATH}")
