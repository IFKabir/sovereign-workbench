import logging

logger = logging.getLogger(__name__)

class TaskRouter:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def classify(self, query: str) -> str:
        if self.model_path:
            return self._onnx_classify(query)
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

    def _onnx_classify(self, query: str) -> str:
        # Mock implementation for ONNX Runtime inference for <5ms latency
        logger.warning("ONNX runtime not fully implemented in fallback, using keyword matching instead.")
        return self._keyword_fallback(query)
