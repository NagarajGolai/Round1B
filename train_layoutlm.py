import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import LayoutLMTokenizer, LayoutLMForTokenClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import ast

MODEL_NAME = 'microsoft/layoutlm-base-uncased'
LABELS = ['body', 'title', 'H1', 'H2', 'H3']
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

class PDFHeadingDataset(Dataset):
    def __init__(self, df, tokenizer):
        self.df = df
        self.tokenizer = tokenizer
    def __len__(self):
        return len(self.df)
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        text = row['text']
        if isinstance(text, str):
            text_to_tokenize = text
        else:
            text_to_tokenize = [text]
        bbox = ast.literal_eval(row['bbox'])
        # Normalize bbox to 0-1000
        bbox = [
            int(bbox[0] / 595 * 1000),
            int(bbox[1] / 842 * 1000),
            int(bbox[2] / 595 * 1000),
            int(bbox[3] / 842 * 1000)
        ]
        encoding = self.tokenizer(
            text_to_tokenize,
            padding='max_length',
            truncation=True,
            max_length=32,
            return_tensors='pt'
        )
        # LayoutLM expects bbox for each token
        encoding['bbox'] = torch.tensor([bbox] * encoding['input_ids'].shape[1])
        label = LABEL2ID.get(row['label'], 0)
        encoding = {k: v.squeeze(0) for k, v in encoding.items()}
        encoding['labels'] = torch.tensor([label] * encoding['input_ids'].shape[0])
        return encoding

def main():
    df = pd.read_csv('training_data.csv')
    # Remove empty text
    df = df[df['text'].str.strip() != '']
    train_df, val_df = train_test_split(df, test_size=0.1, random_state=42)
    tokenizer = LayoutLMTokenizer.from_pretrained(MODEL_NAME)
    train_dataset = PDFHeadingDataset(train_df, tokenizer)
    val_dataset = PDFHeadingDataset(val_df, tokenizer)
    model = LayoutLMForTokenClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID
    )
    training_args = TrainingArguments(
        output_dir='./layoutlm_headings',
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=5,
        evaluation_strategy='epoch',
        save_strategy='epoch',
        logging_dir='./logs',
        learning_rate=5e-5,
        report_to='none',
        fp16=False
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    trainer.train()
    trainer.save_model('./layoutlm_headings')
    print('Model fine-tuned and saved to ./layoutlm_headings')

if __name__ == '__main__':
    main()
