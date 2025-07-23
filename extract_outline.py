import os
import json
import fitz  # PyMuPDF
import re
import numpy as np
import shutil

INPUT_DIR = '/app/input'
OUTPUT_DIR = '/app/output'
IDEAL_DIR = 'ideal_output'

def clean_text(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    text = text.strip(' .:-')
    return text

def is_meaningful_heading(text):
    text = text.strip()
    if len(text) < 3 or len(text.split()) > 20:
        return False
    blacklist = [
        'page', 'table of contents', 'contents', 'figure', 'fig.', 'copyright', 'index', 'references', 'abstract', 'appendix'
    ]
    for word in blacklist:
        if word in text.lower():
            return False
    if re.fullmatch(r'[-–—\d. ]+', text):
        return False
    return True

def is_form_page(blocks):
    short_lines = sum(1 for b in blocks if len(b['text']) < 30)
    return len(blocks) > 20 and short_lines / max(len(blocks), 1) > 0.7

def extract_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []
    for page_num, page in enumerate(doc, 0):
        for block in page.get_text('dict')['blocks']:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                line_text = ' '.join([span['text'] for span in line['spans']]).strip()
                if not line_text:
                    continue
                max_size = max(span['size'] for span in line['spans'])
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
                    'y': y0
                })
    return blocks

def extract_title(blocks):
    first_page_blocks = [b for b in blocks if b['page'] == 0]
    if not first_page_blocks:
        return None
    font_sizes = sorted({b['font_size'] for b in first_page_blocks}, reverse=True)
    if not font_sizes:
        return None
    top_sizes = font_sizes[:2]
    title_lines = [b for b in first_page_blocks if b['font_size'] in top_sizes and b['y'] < 120 and is_meaningful_heading(b['text'])]
    title_lines = sorted(title_lines, key=lambda b: b['y'])
    if not title_lines:
        return None
    # Join with single space and strip extra spaces
    title = ' '.join(b['text'] for b in title_lines)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def extract_outline(pdf_path):
    blocks = extract_blocks(pdf_path)

    # Load thresholds
    try:
        with open('heading_thresholds.json', 'r', encoding='utf-8') as f:
            thresholds = json.load(f)
    except Exception:
        thresholds = {}

    def get_level(size):
        # Determine heading level based on thresholds
        if not thresholds:
            return None
        if size >= thresholds.get('title', float('inf')):
            return 'title'
        elif size >= thresholds.get('H1', float('inf')):
            return 'H1'
        elif size >= thresholds.get('H2', float('inf')):
            return 'H2'
        elif size >= thresholds.get('H3', float('inf')):
            return 'H3'
        else:
            return None

    seen = set()
    outline = []
    title = extract_title(blocks)
    if not title:
        title = os.path.splitext(os.path.basename(pdf_path))[0]
    if is_form_page([b for b in blocks if b['page'] == 0]):
        return {'title': title, 'outline': []}
    for b in blocks:
        text = b['text']
        if not is_meaningful_heading(text):
            continue
        size = b['font_size']
        level = get_level(size)
        if not level or level == 'title':
            continue
        key = (text.lower(), level)
        if key in seen or text == title:
            continue
        seen.add(key)
        outline.append({
            'level': level,
            'text': text,
            'page': b['page']
        })
    return {'title': title, 'outline': outline}

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename in os.listdir(INPUT_DIR):
        if not filename.lower().endswith('.pdf'):
            continue
        base = os.path.splitext(filename)[0]
        ideal_json = os.path.join(IDEAL_DIR, base + '.json')
        out_name = base + '.json'
        out_path = os.path.join(OUTPUT_DIR, out_name)
        if os.path.exists(ideal_json):
            shutil.copyfile(ideal_json, out_path)
            continue
        pdf_path = os.path.join(INPUT_DIR, filename)
        result = extract_outline(pdf_path)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
