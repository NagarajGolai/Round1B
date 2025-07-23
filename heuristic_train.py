import csv
import json
from collections import defaultdict
import numpy as np

TRAINING_CSV = 'training_data.csv'
THRESHOLDS_JSON = 'heading_thresholds.json'

def load_training_data(csv_path):
    font_sizes_by_label = defaultdict(list)
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row['label']
            try:
                bbox = json.loads(row['bbox'].replace("'", '"'))
                font_size = (bbox[3] - bbox[1])  # height of bbox as proxy for font size
                font_sizes_by_label[label].append(font_size)
            except Exception:
                continue
    return font_sizes_by_label

def compute_thresholds(font_sizes_by_label):
    # Compute median font size per label
    medians = {}
    for label, sizes in font_sizes_by_label.items():
        if sizes:
            medians[label] = np.median(sizes)
    # Sort labels by median font size descending (title > H1 > H2 > H3 > body)
    sorted_labels = sorted(medians.items(), key=lambda x: x[1], reverse=True)
    thresholds = {}
    # Assign thresholds between medians to separate heading levels
    for i in range(len(sorted_labels)-1):
        label_current, size_current = sorted_labels[i]
        label_next, size_next = sorted_labels[i+1]
        threshold = (size_current + size_next) / 2
        thresholds[label_current] = threshold
    # Last label threshold set low
    if sorted_labels:
        thresholds[sorted_labels[-1][0]] = 0
    return thresholds

def save_thresholds(thresholds, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(thresholds, f, indent=2)

def main():
    font_sizes_by_label = load_training_data(TRAINING_CSV)
    thresholds = compute_thresholds(font_sizes_by_label)
    save_thresholds(thresholds, THRESHOLDS_JSON)
    print(f"Computed and saved heading thresholds to {THRESHOLDS_JSON}")

if __name__ == '__main__':
    main()
