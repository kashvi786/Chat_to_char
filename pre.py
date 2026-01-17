# # brew install python
# # brew install libxml2 libxslt
# # brew install poppler
# # brew install python@3.11
# # pip install pdfplumber pandas (only in virtual environment)
# # python3 -m venv .venv
# # source .venv/bin/activate

# import pdfplumber
# import re
# import pandas as pd

# PDF_PATH = "/Users/Kashvi-Khurana/CP/3 idiots/3_Idiots.pdf"

# START_PAGE = 20   # page 21 (0-indexed)
# END_PAGE = 318    # exclusive upper bound

# SCENE_PREFIXES = ("EXT.", "INT.")
# SCENE_BLACKLIST = {"DAY", "NIGHT", "CONTINUOUS"}

# # ------------------ helpers ------------------

# def is_english(text):
#     return any(c.isascii() and c.isalpha() for c in text)

# def clean_text(text):
#     return re.sub(r"\s+", " ", text).strip()

# def is_scene_line(line):
#     return line.startswith(SCENE_PREFIXES)

# def is_character_line(line):
#     if not line.isupper():
#         return False
#     if len(line.split()) > 4:
#         return False
#     if line.startswith(SCENE_PREFIXES):
#         return False
#     return True

# def extract_inline_parenthetical(text):
#     """
#     Handles:
#     (disappointed) Forgot my socks.
#     Returns: (tone, cleaned_text)
#     """
#     m = re.match(r"^\(([^)]+)\)\s*(.*)", text)
#     if m:
#         return clean_text(m.group(1)), clean_text(m.group(2))
#     return None, text

# def is_parenthetical_line(line):
#     return line.startswith("(") and line.endswith(")")

# def is_narrative_line(line, current_character):
#     if current_character is None:
#         return True
#     if line.startswith("("):
#         return False
#     if line[0].isupper() and not is_character_line(line):
#         return True
#     return False

# def normalize_character_name(name):
#     """
#     Handles:
#     - FARHAN (V.O.) -> FARHAN
#     - FARHAN V.O.   -> FARHAN
#     - (V.O.) / V.O. -> None (drop)
#     """
#     if name is None:
#         return None

#     name = name.strip()

#     # Pure VO entries → drop
#     if re.fullmatch(r"\(?V\.?O\.?\)?", name, re.IGNORECASE):
#         return None

#     # Remove trailing VO markers
#     name = re.sub(
#         r"\s*\(?V\.?O\.?\)?\s*$",
#         "",
#         name,
#         flags=re.IGNORECASE
#     )

#     name = name.strip()
#     return name if name else None


# def is_vo_only_line(line):
#     return bool(re.fullmatch(r"\(?V\.?O\.?\)?", line, re.IGNORECASE))


# # ------------------ main parser ------------------

# def parse_script(pdf_path):
#     rows = []

#     current_character = None
#     current_scene = None
#     pending_tone = None

#     with pdfplumber.open(pdf_path) as pdf:
#         for page_num in range(START_PAGE, min(END_PAGE, len(pdf.pages))):
#             page = pdf.pages[page_num]

#             words = page.extract_words(use_text_flow=True)
#             if not words:
#                 continue

#             # group words into lines using vertical position
#             lines = {}
#             for w in words:
#                 if not is_english(w["text"]):
#                     continue
#                 key = round(w["top"], 1)
#                 lines.setdefault(key, []).append(w["text"])

#             reconstructed_lines = [
#                 clean_text(" ".join(lines[k]))
#                 for k in sorted(lines.keys())
#             ]

#             for line in reconstructed_lines:
#                 if not line:
#                     continue

#                 # ---- SCENE ----
#                 if is_scene_line(line):
#                     current_scene = line
#                     rows.append({
#                         "page": page_num + 1,
#                         "block_type": "SCENE",
#                         "character": None,
#                         "text": line,
#                         "explicit_tone": None,
#                         "scene": current_scene
#                     })
#                     current_character = None
#                     pending_tone = None
#                     continue

#                 # ---- CHARACTER ----
#                 if is_character_line(line):
#                     normalized = normalize_character_name(line)

#                     # Drop pure VO characters
#                     if normalized is None:
#                         current_character = None
#                         pending_tone = None
#                         continue

#                     current_character = normalized
#                     pending_tone = None
#                     continue

#                 # ---- PARENTHETICAL (tone / direction) ----
#                 if is_parenthetical_line(line):
#                     pending_tone = clean_text(line.strip("()"))
#                     continue

#                 # ---- INLINE TONE ----
#                 inline_tone, cleaned_line = extract_inline_parenthetical(line)
#                 if inline_tone:
#                     pending_tone = inline_tone
#                     line = cleaned_line

#                 # ---- NARRATIVE ----
#                 if is_narrative_line(line, current_character):
#                     rows.append({
#                         "page": page_num + 1,
#                         "block_type": "NARRATIVE",
#                         "character": None,
#                         "text": line,
#                         "explicit_tone": None,
#                         "scene": current_scene
#                     })
#                     continue

#                 # ---- DIALOGUE ----
#                 rows.append({
#                     "page": page_num + 1,
#                     "block_type": "DIALOGUE",
#                     "character": current_character,
#                     "text": line,
#                     "explicit_tone": pending_tone,
#                     "scene": current_scene
#                 })
#                 pending_tone = None

#     df = pd.DataFrame(rows)

#     df["character"] = df["character"].apply(normalize_character_name)
#     df = df.dropna(subset=["character"], how="any")

#     return df

# df = parse_script(PDF_PATH)
# df.to_csv("parsed_script.csv", index=False)

# print(df.head(50))



import pdfplumber
import pandas as pd
import re

PDF_PATH = "3_Idiots.pdf"
OUTPUT_CSV = "exp.csv"

START_PAGE = 21
END_PAGE = 318

def is_scene_line(text: str) -> bool:
    return bool(re.match(r"^(EXT\.|INT\.)", text))


def is_character_line(text: str) -> bool:
    return (
        text.isupper()
        and len(text.split()) <= 4
        and text.isalpha() is False  # allows spaces
    )


def is_tone_line(text: str) -> bool:
    return bool(re.match(r"^\([^)]+\)$", text))


def is_english(text: str) -> bool:
    return all(ord(c) < 128 for c in text)


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

rows = []

current_character = None
current_tone = None
dialogue_buffer = []


def flush_dialogue():
    global dialogue_buffer, current_character, current_tone

    if current_character and dialogue_buffer:
        dialogue = clean_text(" ".join(dialogue_buffer))
        if dialogue:
            rows.append({
                "character": current_character,
                "dialogue": dialogue,
                "tone_of_intent": current_tone
            })

    dialogue_buffer = []
    current_tone = None

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num in range(START_PAGE - 1, END_PAGE):
        page = pdf.pages[page_num]

        lines = page.extract_text(layout=True)
        if not lines:
            continue

        for raw_line in lines.split("\n"):
            line = clean_text(raw_line)

            if not line:
                continue

            # Ignore non-English completely
            if not is_english(line):
                continue

            # Ignore scenes
            if is_scene_line(line):
                flush_dialogue()
                current_character = None
                continue

            # Character line
            if is_character_line(line):
                flush_dialogue()
                current_character = line
                continue

            # Tone line
            if is_tone_line(line):
                current_tone = line.strip("()").lower()
                continue

            # Dialogue line
            if current_character:
                dialogue_buffer.append(line)

# Flush final buffer
flush_dialogue()

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_CSV, index=False)

print(f"Saved {len(df)} dialogues to {OUTPUT_CSV}")