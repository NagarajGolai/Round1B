import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def rank_sections(documents, persona, job_to_be_done, extracted_outlines, pdf_texts):
    """
    Rank extracted sections based on relevance to persona and job_to_be_done using TF-IDF cosine similarity.
    Args:
        documents: list of document filenames
        persona: string describing the persona role
        job_to_be_done: string describing the job/task
        extracted_outlines: dict mapping document filename to extracted outline dict
        pdf_texts: dict mapping document filename to full text content
    Returns:
        output dict with metadata, extracted_sections with importance_rank, and subsection_analysis
    """
    # Prepare corpus for TF-IDF: combine persona and job description as query
    query = persona + " " + job_to_be_done

    # Collect section texts and metadata
    section_texts = []
    section_meta = []
    for doc in documents:
        outline = extracted_outlines.get(doc, {})
        sections = outline.get('outline', [])
        full_text = pdf_texts.get(doc, "")
        for sec in sections:
            # Extract section title and page number
            title = sec.get('text', '')
            page = sec.get('page', -1)
            # Extract subsection text: for simplicity, extract all text from that page
            # In real scenario, could extract text within section bbox or between headings
            # Here, we split full_text by pages assuming page breaks marked by '\f'
            pages = full_text.split('\\f')
            if 0 <= page < len(pages):
                refined_text = pages[page].strip()
            else:
                refined_text = ""
            section_texts.append(title + " " + refined_text)
            section_meta.append({
                'document': doc,
                'section_title': title,
                'page_number': page,
                'refined_text': refined_text
            })

    # Vectorize query and sections
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    corpus = [query] + section_texts
    tfidf_matrix = vectorizer.fit_transform(corpus)
    query_vec = tfidf_matrix[0]
    section_vecs = tfidf_matrix[1:]

    # Compute cosine similarity scores
    scores = cosine_similarity(query_vec, section_vecs).flatten()

    # Rank sections by score descending
    ranked_indices = np.argsort(-scores)

    # Prepare output extracted_sections and subsection_analysis with importance_rank
    extracted_sections = []
    subsection_analysis = []
    for rank, idx in enumerate(ranked_indices, start=1):
        meta = section_meta[idx]
        extracted_sections.append({
            'document': meta['document'],
            'section_title': meta['section_title'],
            'importance_rank': rank,
            'page_number': meta['page_number']
        })
        subsection_analysis.append({
            'document': meta['document'],
            'refined_text': meta['refined_text'],
            'page_number': meta['page_number']
        })

    output = {
        'metadata': {
            'input_documents': documents,
            'persona': persona,
            'job_to_be_done': job_to_be_done
        },
        'extracted_sections': extracted_sections,
        'subsection_analysis': subsection_analysis
    }
    return output
