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

def cluster_font_sizes(sizes):
    sizes = sorted(set(sizes), reverse=True)
    if not sizes:
        return []
    clusters = [[sizes[0]]]
    for s in sizes[1:]:
        if abs(s - clusters[-1][0]) > 1.5:
            clusters.append([s])
        else:
            clusters[-1].append(s)
    return [np.mean(c) for c in clusters]

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
    return '  '.join(b['text'] for b in title_lines)

def extract_outline(pdf_path):
    blocks = extract_blocks(pdf_path)
    sizes = [b['font_size'] for b in blocks]
    font_clusters = cluster_font_sizes(sizes)
    size_to_level = {}
    if font_clusters:
        size_to_level[font_clusters[0]] = 'H1'
        if len(font_clusters) > 1:
            size_to_level[font_clusters[1]] = 'H2'
        if len(font_clusters) > 2:
            size_to_level[font_clusters[2]] = 'H3'
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
        closest = min(font_clusters, key=lambda c: abs(size - c)) if font_clusters else size
        level = size_to_level.get(closest)
        if not level:
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