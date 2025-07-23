import os
import json
import fitz
import torch
from transformers import LayoutLMv2Processor, LayoutLMv2ForTokenClassification
import numpy as np
import re

INPUT_DIR = 'input'
OUTPUT_DIR = 'output'
MODEL_DIR = './layoutlmv2_headings'
LABELS = ['body', 'title', 'H1', 'H2', 'H3']
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

def clean_text(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    text = text.strip(' .:-')
    return text

def extract_words_and_boxes(pdf_path):
    doc = fitz.open(pdf_path)
    words = []
    boxes = []
    page_map = []
    for page_num, page in enumerate(doc):
        width, height = page.rect.width, page.rect.height
        blocks = page.get_text("blocks")
        for b in blocks:
            x0, y0, x1, y1, text, block_no = b[:6]
            if not text.strip():
                continue
            for word in text.split():
                word = clean_text(word)
                if not word:
                    continue
                words.append(word)
                box = [int(x0), int(y0), int(x1), int(y1)]
                boxes.append(box)
                page_map.append(page_num)
    return words, boxes, page_map

def normalize_bbox(box, width, height):
    return [
        int(1000 * (box[0] / width)),
        int(1000 * (box[1] / height)),
        int(1000 * (box[2] / width)),
        int(1000 * (box[3] / height)),
    ]

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    processor = LayoutLMv2Processor.from_pretrained(MODEL_DIR)
    model = LayoutLMv2ForTokenClassification.from_pretrained(MODEL_DIR)
    model.to(device)
    model.eval()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filename in os.listdir(INPUT_DIR):
        if not filename.lower().endswith('.pdf'):
            continue
        pdf_path = os.path.join(INPUT_DIR, filename)
        doc = fitz.open(pdf_path)
        words = []
        boxes = []
        page_map = []
        for page_num, page in enumerate(doc):
            width, height = page.rect.width, page.rect.height
            blocks = page.get_text("blocks")
            for b in blocks:
                x0, y0, x1, y1, text, block_no = b[:6]
                if not text.strip():
                    continue
                for word in text.split():
                    word = clean_text(word)
                    if not word:
                        continue
                    words.append(word)
                    box = normalize_bbox([x0, y0, x1, y1], width, height)
                    boxes.append(box)
                    page_map.append(page_num)

        if not words:
            continue

        encoding = processor(words, boxes=boxes, return_tensors="pt", padding="max_length", truncation=True, max_length=512)
        encoding = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = model(**encoding)
        logits = outputs.logits
        predictions = torch.argmax(logits, dim=2).squeeze().tolist()

        # Aggregate predictions by page and text
        outline = []
        seen = set()
        title = None
        for word, pred, page_num in zip(words, predictions, page_map):
            label = ID2LABEL.get(pred, 'body')
            if label == 'title' and title is None:
                title = word
            if label in ['H1', 'H2', 'H3']:
                key = (word.lower(), label, page_num)
                if key not in seen:
                    seen.add(key)
                    outline.append({
                        'level': label,
                        'text': word,
                        'page': page_num
                    })
        if title is None:
            title = os.path.splitext(filename)[0]

        # Sort outline by page and text
        outline = sorted(outline, key=lambda x: (x['page'], x['text']))

        result = {
            'title': title,
            'outline': outline
        }

        out_path = os.path.join(OUTPUT_DIR, os.path.splitext(filename)[0] + '.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
