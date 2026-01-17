import re
import pandas as pd

MSG_PATTERN = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s(.+?)\]\s([^:]+):\s(.*)"
)
# MSG_PATTERN = re.compile(
#     r"^(\d{1,2}/\d{1,2}/\d{4}),\s(\d{1,2}:\d{2})\s-\s([^:]+):\s(.*)"
# )

SYSTEM_MARKERS = [
    "Messages and calls are end-to-end encrypted",
    "added you",
    "changed the group name",
    "image omitted",
    "video omitted",
    "sticker omitted",
]

def is_system_message(text):
    return any(m.lower() in text.lower() for m in SYSTEM_MARKERS)

def parse_whatsapp_chat(path):
    rows = []
    current_user = None
    current_text = ""

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            m = MSG_PATTERN.match(line)

            if m:
                if current_user and current_text and not is_system_message(current_text):
                    rows.append({
                        "person": current_user,
                        "text_raw": current_text.strip()
                    })

                current_user = m.group(3).strip()
                current_text = m.group(4).strip()
            else:
                current_text += " " + line

        if current_user and current_text and not is_system_message(current_text):
            rows.append({
                "person": current_user,
                "text_raw": current_text.strip()
            })

    df = pd.DataFrame(rows)
    df = df[df["text_raw"].str.len() > 3]  # drop trivial msgs
    return df

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


CHAT_PATH = "_chat.txt"
# OUT_PATH = "whatsapp_translated.csv"

MODEL_NAME = "facebook/nllb-200-distilled-600M"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

def translate_batch(texts, batch_size=16):
    outputs = []

    target_lang = "eng_Latn"
    tokenizer.src_lang = "hin_Deva"  # works for Hindi + Hinglish

    forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang)

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        inputs = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        translated = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=128
        )

        outputs.extend(
            tokenizer.batch_decode(translated, skip_special_tokens=True)
        )

    return outputs

def main():
    df = parse_whatsapp_chat(CHAT_PATH)

    print(f"Translating {len(df)} messages...")
    df["text_en"] = translate_batch(df["text_raw"].tolist())

    df[["person", "text_raw", "text_en"]].to_csv(
        "whatsapp_translated.csv", index=False
    )

    print(f"Saved translated chat to whatsapp_translated.csv")

if __name__ == "__main__":
    main()
