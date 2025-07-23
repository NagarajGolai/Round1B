#!/bin/sh
set -e

echo "Preparing training data..."
python prepare_training_data.py

echo "Training LayoutLMv2 model..."
python train_layoutlmv2.py

echo "Running inference on input PDFs..."
python infer_layoutlm.py

echo "Pipeline completed."
