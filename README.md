# Round 1B - PDF Section Extraction and Ranking

## Overview
This project extracts and ranks relevant sections from a set of PDF documents based on a given persona and job-to-be-done, outputting the results in a structured JSON format.

## Requirements
- Docker (recommended)
- Or: Python 3.10+, pip, and the dependencies in `requirements.txt`

## Input Format
Place your input PDFs in the `input/` folder. The input JSON (`input/challenge1b_input.json`) should look like:

```
{
  "challenge_info": {
    "challenge_id": "round_1b_002",
    "test_case_name": "travel_planner",
    "description": "France Travel"
  },
  "documents": [
    { "filename": "South of France - Cities.pdf", "title": "South of France - Cities" },
    { "filename": "South of France - Cuisine.pdf", "title": "South of France - Cuisine" }
    // ... more documents ...
  ],
  "persona": { "role": "Travel Planner" },
  "job_to_be_done": { "task": "Plan a trip of 4 days for a group of 10 college friends." }
}
```

## Output Format
The output JSON (`output/challenge1b_output.json`) will include:
- `metadata` (with processing timestamp)
- `extracted_sections` (ranked relevant sections)
- `subsection_analysis` (detailed extracted text)

## How to Build and Run with Docker
1. **Build the Docker image:**
   ```sh
   docker build -t round1b-pipeline .
   ```
2. **Run the pipeline:**
   ```sh
   docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" round1b-pipeline
   ```
   - This will process the PDFs listed in your input JSON and write the output to `output/challenge1b_output.json`.

## Dependencies
- pymupdf
- numpy
- scikit-learn

## Notes
- Make sure your PDFs are present in the `input/` folder and listed in the input JSON.
- The output folder will be created if it does not exist.
- For custom test cases, update the input JSON accordingly.
