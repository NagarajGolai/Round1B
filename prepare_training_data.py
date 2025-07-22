import os
import fitz
import json
import csv
import re

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

def extract_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []
    for page_num, page in enumerate(doc, 0):
        width, height = page.rect.width, page.rect.height
        for block in page.get_text('dict')['blocks']:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                line_text = ' '.join([span['text'] for span in line['spans']]).strip()
                if not line_text:
                    continue
                max_size = max(span['size'] for span in line['spans'])
                is_bold = any('bold' in span['font'].lower() for span in line['spans'])
                x0 = min(span['bbox'][0] for span in line['spans'])
                y0 = min(span['bbox'][1] for span in line['spans'])
                x1 = max(span['bbox'][2] for span in line['spans'])
                y1 = max(span['bbox'][3] for span in line['spans'])
                bbox = [int(x0), int(y0), int(x1), int(y1)]
                blocks.append({
                    'page': page_num,
                    'text': clean_text(line_text),
                    'bbox': bbox,
                    'font_size': max_size,
                    'bold': is_bold
                })
    return blocks

def main():
    input_dir = 'input'
    ideal_dir = 'ideal_output'
    out_csv = 'training_data.csv'
    rows = []
    for pdf_file in os.listdir(input_dir):
        if not pdf_file.lower().endswith('.pdf'):
            continue
        base = os.path.splitext(pdf_file)[0]
        ideal_json = os.path.join(ideal_dir, base + '.json')
        if not os.path.exists(ideal_json):
            continue
        title, headings = load_ideal_labels(ideal_json)
        blocks = extract_blocks(os.path.join(input_dir, pdf_file))
        for block in blocks:
            label = 'body'
            if (block['text'], block['page']) in headings:
                label = headings[(block['text'], block['page'])]
            elif block['text'] == title:
                label = 'title'
            rows.append({
                'pdf': pdf_file,
                'page': block['page'],
                'text': block['text'],
                'bbox': block['bbox'],
                'font_size': block['font_size'],
                'bold': block['bold'],
                'label': label
            })
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['pdf', 'page', 'text', 'bbox', 'font_size', 'bold', 'label'])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Wrote {len(rows)} rows to {out_csv}")

if __name__ == '__main__':
    main() 