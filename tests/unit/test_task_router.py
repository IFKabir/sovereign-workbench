import time
import pytest
from agent_core.router import TaskRouter

@pytest.fixture(scope="module")
def router():
    r = TaskRouter()
    r.predict("Warmup diagnostic query")
    return r

@pytest.mark.parametrize("query,expected_intent", [
    ("What is the minimum safe distance between a furnace and a tank under OISD-118?", "RAG_STANDARDS"),
    ("Verify if the bypass line on Valve CV-101 violates double block and bleed rules", "VISION_SCHEMATIC"),
    ("Write a Python script to calculate pressure drop across a 50m pipe", "CODE_SANDBOX"),
    ("Summarize the equipment issues listed in the night shift handover report", "DOC_REASONING"),
    ("hi", "GENERAL_CHAT"),
])
def test_intent_classification_accuracy(router: TaskRouter, query: str, expected_intent: str):
    predicted_intent = router.predict(query)
    assert predicted_intent == expected_intent

def test_router_inference_latency_benchmark(router: TaskRouter):
    test_queries = [
        "Check valve status on CDU P&ID",
        "Calculate Darcy friction factor for Reynolds number 4000",
        "Explain hot work permit isolation requirements in OISD-105",
        "Extract table from maintenance log"
    ]
    latencies = []
    for query in test_queries:
        start = time.perf_counter()
        router.predict(query)
        duration_ms = (time.perf_counter() - start) * 1000
        latencies.append(duration_ms)
    
    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 100.0, f"Average latency {avg_latency:.2f}ms exceeded SLA target"
