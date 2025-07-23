import os
import fitz
import json
import csv
import re
from transformers import LayoutLMv2Processor

def clean_text(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    text = text.strip(' .:-')
    return text

def load_ideal_labels(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    title = clean_text(data.get('title', ''))
    outline = data.get('outline', [])
    headings = {}
    for h in outline:
        key = (clean_text(h['text']), h['page'])
        headings[key] = h['level']
    return title, headings

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
                # Approximate bbox for each word using block bbox
                boxes.append([int(x0), int(y0), int(x1), int(y1)])
                page_map.append(page_num)
    return words, boxes, page_map

def main():
    input_dir = 'input'
    ideal_dir = 'ideal_output'
    out_csv = 'training_data.csv'
    rows = []
    processed_files = 0
    for pdf_file in os.listdir(input_dir):
        if not pdf_file.lower().endswith('.pdf'):
            continue
        base = os.path.splitext(pdf_file)[0]
        ideal_json = os.path.join(ideal_dir, base + '.json')
        if not os.path.exists(ideal_json):
            print(f"Warning: No ideal output JSON for {pdf_file}")
            continue
        processed_files += 1
        title, headings = load_ideal_labels(ideal_json)
        words, boxes, page_map = extract_words_and_boxes(os.path.join(input_dir, pdf_file))
        file_rows = 0
        for word, box, page_num in zip(words, boxes, page_map):
            label = 'body'
            clean_word = clean_text(word)
            key = (clean_word, page_num)
            if key in headings:
                label = headings[key]
            elif clean_word == title:
                label = 'title'
            rows.append({
                'pdf': pdf_file,
                'page': page_num,
                'text': clean_word,
                'bbox': box,
                'label': label
            })
            file_rows += 1
        print(f"Processed {pdf_file}: {file_rows} rows")
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['pdf', 'page', 'text', 'bbox', 'label']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Processed {processed_files} files")
    print(f"Wrote {len(rows)} rows to {out_csv}")

if __name__ == '__main__':
    main()
