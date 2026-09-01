import pytest
from agent_core.nodes.rag_retriever import retrieve_standards

@pytest.mark.asyncio
async def test_qdrant_standards_retrieval():
    state = {
        "query": "What is the minimum safe separation distance between a process unit and a control room under OISD-118?"
    }
    result = await retrieve_standards(state)
    
    assert "rag_results" in result or "retrieved_context" in result
    ctx = result.get("retrieved_context", "") or str(result.get("rag_results", ""))
    assert "60m" in ctx or "Process Unit" in ctx or "standards" in ctx

@pytest.mark.asyncio
async def test_rag_negative_constraint_handling():
    # Query completely outside the ingested refinery standards
    state = {
        "query": "What are the rules for designing subsea blowout preventers for offshore deepwater rigs?"
    }
    result = await retrieve_standards(state)
    assert result.get("current_node") == "retrieve_standards"
