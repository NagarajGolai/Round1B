
# Round 1B: Persona-Driven Document Intelligence
### Theme: “Connect What Matters — For the User Who Matters”
### Challenge Brief
You will build a system that acts as an intelligent document analyst, extracting and prioritizing the most relevant sections from a collection of documents based on a specific persona and their job-to-be-done.

### Input Specification
Document Collection: 3 - 10 related PDFs

Persona Definition: Role description with specific expertise and focus areas

Job-to-be-Done: Concrete task the persona needs to accomplish

Your system must generalize across different domains and personas.

### 🛠️ Build Docker Image

```bash
docker build --platform linux/amd64 -t pdf-outline-extractor:latest .
```

## Run with Docker

###
▶️Run the Pipeline

Mac/Linux:
```
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" round1b-pipeline
```
Windows PowerShell:
```
docker run --rm -v "${PWD}\input:/app/input" -v "${PWD}\output:/app/output" round1b-pipeline
```
Windows CMD:
```
docker run --rm -v "%cd%\input:/app/input" -v "%cd%\output:/app/output" round1b-pipeline
```
### Execution time :

Docker build time : < 15 seconds
Docker image run time : < 10 seconds

## Note :
This system runs completely offline once built. However, an internet connection is required only while building the Docker image (to download dependencies). After that, it can be run without internet access.
