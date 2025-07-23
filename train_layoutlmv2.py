import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import LayoutLMv2Processor, LayoutLMv2ForTokenClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import ast
import numpy as np

MODEL_NAME = 'microsoft/layoutlmv2-base-uncased'
LABELS = ['body', 'title', 'H1', 'H2', 'H3']
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

class PDFHeadingDataset(Dataset):
    def __init__(self, df, processor):
        self.df = df
        self.processor = processor
        self.grouped = self.df.groupby(['pdf', 'page'])
        self.keys = list(self.grouped.groups.keys())

    def __len__(self):
        return len(self.keys)

    def __getitem__(self, idx):
        key = self.keys[idx]
        group = self.grouped.get_group(key)
        words = group['text'].tolist()
        boxes = group['bbox'].apply(ast.literal_eval).tolist()
        labels = [LABEL2ID[label] for label in group['label'].tolist()]

        encoding = self.processor(
            words,
            boxes=boxes,
            padding='max_length',
            truncation=True,
            max_length=512,
            return_tensors='pt'
        )
        # LayoutLMv2 expects bbox for each token, so we replicate boxes per token
        # But processor already handles this internally, so no need to manually replicate

        # Prepare labels aligned with tokens
        word_ids = encoding.word_ids(batch_index=0)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(labels[word_idx])
            else:
                # For tokens inside a word, assign label -100 to ignore in loss
                label_ids.append(-100)
            previous_word_idx = word_idx

        item = {k: v.squeeze(0) for k, v in encoding.items()}
        item['labels'] = torch.tensor(label_ids)
        return item

def main():
    df = pd.read_csv('training_data.csv')
    # Remove empty text rows if any
    df = df[df['text'].str.strip() != '']
    train_df, val_df = train_test_split(df, test_size=0.1, random_state=42)
    processor = LayoutLMv2Processor.from_pretrained(MODEL_NAME)
    train_dataset = PDFHeadingDataset(train_df, processor)
    val_dataset = PDFHeadingDataset(val_df, processor)
    model = LayoutLMv2ForTokenClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID
    )
    training_args = TrainingArguments(
        output_dir='./layoutlmv2_headings',
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        num_train_epochs=1,
        evaluation_strategy='no',
        save_strategy='no',
        logging_dir='./logs',
        learning_rate=5e-5,
        report_to='none',
        fp16=False,
        save_total_limit=1,
        load_best_model_at_end=False,
        metric_for_best_model=None,
        greater_is_better=False
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    trainer.train()
    trainer.save_model('./layoutlmv2_headings')
    print('Model fine-tuned and saved to ./layoutlmv2_headings')

if __name__ == '__main__':
    main()
