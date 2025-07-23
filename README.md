# PDF Outline Extractor using Heuristic Approach

## Overview

This project implements a PDF outline extractor that uses a heuristic approach based on font sizes and positions extracted via PyMuPDF (`fitz`). The solution processes all PDFs in the `/app/input` directory and outputs corresponding JSON files in `/app/output` with the extracted outline in a structured format.

## Approach

- Uses PyMuPDF (`fitz`) to extract text blocks, font sizes, and positions from PDF pages.
- Infers heading levels (H1, H2, H3) and title based on font size thresholds.
- Thresholds are computed from training data using a heuristic training script.
- Outputs JSON files with the format:
  ```json
  {
    "title": "Document Title",
    "outline": [
      { "level": "H1", "text": "Introduction", "page": 1 },
      { "level": "H2", "text": "Subsection", "page": 2 },
      { "level": "H3", "text": "Detail", "page": 3 }
    ]
  }
  ```

## Dependencies

- Python 3.10
- PyMuPDF
- numpy

## Docker

The project includes a Dockerfile to build a containerized environment for easy deployment.

### Build Docker Image

```bash
docker build --platform linux/amd64 -t pdf-outline-extractor:latest .
```

### Run Docker Container

```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-outline-extractor:latest
```

This command processes all PDFs in the `input` folder and writes JSON outputs to the `output` folder.

## Assumptions and Notes

- The solution uses a heuristic approach without deep learning models.
- The solution runs on CPU only.
- The solution does not make any network calls and runs offline.
- The processing time for a 50-page PDF should be under 10 seconds on a system with 8 CPUs and 16 GB RAM.
- The Docker image is based on `python:3.10-slim` with AMD64 platform compatibility.

## How to Train Thresholds

- Use the `heuristic_train.py` script to compute font size thresholds from the training data CSV (`training_data.csv`).
- The script outputs `heading_thresholds.json` which is used by the extractor to assign heading levels.

## How to Extend

- To prepare training data, use `prepare_training_data.py`.
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none pdf-outline-extractor:latest
