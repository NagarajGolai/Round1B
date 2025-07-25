import os
import json
import fitz  # PyMuPDF
from relevance_ranker import rank_sections
import re

INPUT_JSON = 'input/challenge1b_input.json'
OUTPUT_JSON = 'output/challenge1b_output.json'
INPUT_DIR = 'input'

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
    seen = set()
    outline = []
    title = extract_title(blocks)
    if not title:
        title = os.path.splitext(os.path.basename(pdf_path))[0]
    # Find top 3 font sizes on each page
    page_font_sizes = {}
    for b in blocks:
        page_font_sizes.setdefault(b['page'], []).append(b['font_size'])
    for page in page_font_sizes:
        sizes = sorted(set(page_font_sizes[page]), reverse=True)
        page_font_sizes[page] = sizes[:3]
    prev_level = None
    prev_text = None
    prev_page = None
    for b in blocks:
        text = b['text']
        if not is_meaningful_heading(text):
            continue
        # Only consider headings with top 3 font sizes on the page
        if b['font_size'] not in page_font_sizes[b['page']]:
            continue
        # Only consider headings that are not too long and look like titles
        if len(text.split()) > 10:
            continue
        if text.endswith('.') or text.endswith(',') or text.endswith(';'):
            continue
        size = b['font_size']
        if size > 15:
            level = 'H1'
        elif size > 12:
            level = 'H2'
        elif size > 9:
            level = 'H3'
        else:
            level = None
        if not level or level == 'title':
            continue
        key = (text.lower(), level)
        if key in seen or text == title:
            continue
        # Group consecutive headings of the same level
        if prev_level == level and prev_page == b['page']:
            prev_text += ' ' + text
            outline[-1]['text'] = prev_text
        else:
            outline.append({
                'level': level,
                'text': text,
                'page': b['page']
            })
            prev_text = text
            prev_level = level
            prev_page = b['page']
        seen.add(key)
    return {'title': title, 'outline': outline}

def load_input_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_output_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    # Join pages with form feed character to separate pages
    return '\f'.join(texts)

def main():
    # Load input JSON with documents, persona, job_to_be_done
    input_data = load_input_json(INPUT_JSON)
    documents_info = input_data.get('documents', [])
    persona_info = input_data.get('persona', {})
    job_info = input_data.get('job_to_be_done', {})

    documents = [doc['filename'] for doc in documents_info]
    persona = persona_info.get('role', '')
    job_to_be_done = job_info.get('task', '')

    # Extract outlines for each document
    extracted_outlines = {}
    pdf_texts = {}
    for doc in documents:
        pdf_path = os.path.join(INPUT_DIR, doc)
        outline = extract_outline(pdf_path)
        extracted_outlines[doc] = outline
        pdf_texts[doc] = load_pdf_text(pdf_path)

    # Rank sections based on persona and job_to_be_done
    output = rank_sections(documents, persona, job_to_be_done, extracted_outlines, pdf_texts)

    # Add processing timestamp to metadata
    from datetime import datetime
    output['metadata']['processing_timestamp'] = datetime.utcnow().isoformat()

    # Save output JSON
    save_output_json(output, OUTPUT_JSON)
    print(f"Output saved to {OUTPUT_JSON}")

if __name__ == '__main__':
    main()
