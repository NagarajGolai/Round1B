# Adobe Hackathon Round 1A: PDF Outline Extractor

## Overview
This solution extracts a structured outline (title, H1, H2, H3 headings) from all PDF files in `/app/input` and outputs a corresponding JSON for each in `/app/output`, as per the challenge requirements.

## Usage

### 1. Build the Docker Image
```
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

### 2. Run the Docker Container
```
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
```

- Place your PDF files in the `input` directory.
- The output JSON files will appear in the `output` directory, one per PDF.

## Constraints
- Compatible with AMD64 (x86_64) architecture
- No GPU dependencies
- Model size (if used) ≤ 200MB
- Works fully offline (no network calls)
- Processes a 50-page PDF in ≤ 10 seconds

## Output Format
```
{
  "title": "Document Title",
  "outline": [
    { "level": "H1", "text": "Section 1", "page": 1 },
    { "level": "H2", "text": "Subsection", "page": 2 },
    { "level": "H3", "text": "Subsubsection", "page": 3 }
  ]
}
```

## Dependencies
- Python 3.10
- PyMuPDF

## Notes
- The solution uses heuristics based on font size, boldness, and capitalization to detect headings.
- If no title is found, the PDF metadata or filename is used as a fallback. 