import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

GREETINGS = {
    "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
    "good evening", "who are you", "help", "what can you do", "system status",
    "hi there", "hello there", "test"
}

class TaskRouter:
    def __init__(self, model_dir: str | None = None):
        if model_dir is None:
            # Default to models/task-router if present
            root = Path(__file__).parent.parent.parent.parent
            candidate = root / "models" / "task-router"
            if candidate.exists():
                model_dir = str(candidate)

        self.model_dir = model_dir
        self.session = None
        self.tokenizer = None
        self.id2label = {0: "DOC_REASONING", 1: "CODE_SANDBOX", 2: "VISION_SCHEMATIC", 3: "RAG_STANDARDS"}

        if self.model_dir and os.path.exists(os.path.join(self.model_dir, "model.onnx")):
            try:
                import onnxruntime as ort
                from transformers import AutoTokenizer

                onnx_path = os.path.join(self.model_dir, "model.onnx")
                label_path = os.path.join(self.model_dir, "label_mapping.json")
                tokenizer_dir = os.path.join(self.model_dir, "pytorch_model")

                if os.path.exists(label_path):
                    with open(label_path, "r") as f:
                        mapping = json.load(f)
                        self.id2label = {int(k): v for k, v in mapping.get("id2label", {}).items()}

                opts = ort.SessionOptions()
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

                self.session = ort.InferenceSession(onnx_path, opts)
                tok_path = tokenizer_dir if os.path.exists(tokenizer_dir) else "answerdotai/ModernBERT-base"
                self.tokenizer = AutoTokenizer.from_pretrained(tok_path)

                # JIT Warmup (1-2 dummy inference passes)
                self._warmup()
                logger.info("TaskRouter: ONNX model loaded and JIT pre-warmed successfully.")
            except Exception as e:
                logger.warning(f"TaskRouter: Failed to load ONNX model ({e}). Using keyword fallback.")

    def _warmup(self):
        if self.session and self.tokenizer:
            try:
                dummy_input = self.tokenizer("System diagnostic warmup query", return_tensors="np", padding="max_length", max_length=128, truncation=True)
                for _ in range(2):
                    self.session.run(None, {
                        "input_ids": dummy_input["input_ids"],
                        "attention_mask": dummy_input["attention_mask"]
                    })
            except Exception as e:
                logger.warning(f"TaskRouter warmup exception: {e}")

    def classify(self, query: str) -> str:
        return self.predict(query)

    def predict(self, query: str) -> str:
        q_clean = query.strip().lower().rstrip("!?.")
        if q_clean in GREETINGS or any(q_clean.startswith(g + " ") for g in ["hi", "hello", "hey"]):
            return "GENERAL_CHAT"

        if self.session and self.tokenizer:
            try:
                inputs = self.tokenizer(query, return_tensors="np", padding="max_length", max_length=128, truncation=True)
                outputs = self.session.run(None, {
                    "input_ids": inputs["input_ids"],
                    "attention_mask": inputs["attention_mask"]
                })
                import numpy as np
                predicted_id = int(np.argmax(outputs[0], axis=-1)[0])
                return self.id2label.get(predicted_id, "DOC_REASONING")
            except Exception as e:
                logger.error(f"ONNX classification error ({e}), falling back to keywords.")

        return self._keyword_fallback(query)

    def _keyword_fallback(self, query: str) -> str:
        q = query.lower()
        vision_keywords = ['p&id', 'piping', 'diagram', 'schematic', 'symbol', 'drawing', 'instrumentation', 'valve', 'pump', 'flowsheet', 'isometric']
        code_keywords = ['calculate', 'compute', 'python', 'script', 'formula', 'equation', 'simulate', 'model', 'optimize', 'blend']
        rag_keywords = ['standard', 'oisd', 'pngrb', 'regulation', 'compliance', 'safety', 'permit', 'procedure', 'specification', 'is code', 'api standard']

        if any(kw in q for kw in vision_keywords):
            return "VISION_SCHEMATIC"
        elif any(kw in q for kw in code_keywords):
            return "CODE_SANDBOX"
        elif any(kw in q for kw in rag_keywords):
            return "RAG_STANDARDS"

        return "DOC_REASONING"
