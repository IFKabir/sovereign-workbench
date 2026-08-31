"""Fine-tune answerdotai/ModernBERT-base for industrial task routing.

Trains a sequence classification model to route user queries to the
appropriate agent node: DOC_REASONING, CODE_SANDBOX, VISION_SCHEMATIC,
or RAG_STANDARDS. Exports both PyTorch and ONNX checkpoints for
sub-5ms CPU inference in the sovereign workbench.

Designed for MRPL SIH26117 — all training runs locally, zero cloud deps.
"""

import json
import os
import torch
import numpy as np
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
import onnx

def load_data(data_dir: str) -> DatasetDict:
    """Loads JSONL data into a HuggingFace DatasetDict."""
    def load_jsonl(path):
        with open(path, 'r') as f:
            return [json.loads(line) for line in f]
            
    train_data = load_jsonl(os.path.join(data_dir, "train.jsonl"))
    val_data = load_jsonl(os.path.join(data_dir, "val.jsonl"))
    
    # Convert category_id to label for HuggingFace Trainer
    for item in train_data:
        item["label"] = item.pop("category_id")
    for item in val_data:
        item["label"] = item.pop("category_id")
        
    return DatasetDict({
        "train": Dataset.from_list(train_data),
        "validation": Dataset.from_list(val_data)
    })

def compute_metrics(eval_pred):
    """Computes accuracy, precision, recall, and F1 score."""
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='macro')
    acc = accuracy_score(labels, predictions)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def train_and_export():
    """Main function to train and export the model."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_name = "answerdotai/ModernBERT-base"
    output_dir = os.path.join(base_dir, "../../models/task-router")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load dataset
    print("Loading dataset...")
    dataset = load_data(base_dir)
    
    # Load tokenizer and tokenize data
    print("Tokenizing data...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)
        
    tokenized_datasets = dataset.map(tokenize_function, batched=True)
    
    # Define labels
    id2label = {0: "DOC_REASONING", 1: "CODE_SANDBOX", 2: "VISION_SCHEMATIC", 3: "RAG_STANDARDS"}
    label2id = {v: k for k, v in id2label.items()}
    
    # Save label mapping
    with open(os.path.join(output_dir, "label_mapping.json"), "w") as f:
        json.dump({"id2label": id2label, "label2id": label2id}, f)
    
    # Load model
    print("Loading model...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=4, 
        id2label=id2label, 
        label2id=label2id
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=os.path.join(base_dir, "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=32,
        num_train_epochs=4,
        weight_decay=0.01,
        warmup_steps=50,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        fp16=torch.cuda.is_available(),
        logging_steps=10
    )
    
    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )
    
    # Train
    print("Starting training...")
    trainer.train()
    
    # Evaluate
    print("Evaluating...")
    eval_results = trainer.evaluate()
    print(f"Evaluation results: {eval_results}")
    
    # Generate classification report
    predictions = trainer.predict(tokenized_datasets["validation"])
    preds = np.argmax(predictions.predictions, axis=-1)
    labels = predictions.label_ids
    target_names = [id2label[i] for i in range(4)]
    print("\nClassification Report:")
    print(classification_report(labels, preds, target_names=target_names))
    
    # Save PyTorch checkpoint
    print("Saving PyTorch model...")
    trainer.save_model(os.path.join(output_dir, "pytorch_model"))
    
    # Export to ONNX
    print("Exporting to ONNX...")
    model.eval()
    dummy_input = tokenizer("Test sequence for ONNX export", return_tensors="pt", padding="max_length", max_length=128, truncation=True)
    if torch.cuda.is_available():
        model = model.cpu() # Export on CPU
    
    input_ids = dummy_input["input_ids"]
    attention_mask = dummy_input["attention_mask"]
    
    onnx_path = os.path.join(output_dir, "model.onnx")
    torch.onnx.export(
        model,
        (input_ids, attention_mask),
        onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size"}
        },
        opset_version=14,
        do_constant_folding=True
    )
    print(f"ONNX model saved to {onnx_path}")
    print("Training and export complete!")

if __name__ == "__main__":
    train_and_export()
