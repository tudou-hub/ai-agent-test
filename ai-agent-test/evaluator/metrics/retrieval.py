from typing import List, Dict, Any
from collections import Counter
import re


class RetrievalMetrics:
    def __init__(self, top_k: int = 3):
        self.top_k = top_k
    
    def calculate_hit_rate(self, retrieved_chunks: List[Dict], expected_keys: List[str]) -> float:
        if not expected_keys or not retrieved_chunks:
            return 0.0
        
        combined_text = " ".join([chunk.get("content", "") for chunk in retrieved_chunks]).lower()
        hits = sum(1 for key in expected_keys if key.lower() in combined_text)
        return hits / len(expected_keys)
    
    def calculate_mrr(self, retrieved_chunks: List[Dict], expected_keys: List[str]) -> float:
        if not expected_keys or not retrieved_chunks:
            return 0.0
        
        for rank, chunk in enumerate(retrieved_chunks, 1):
            content = chunk.get("content", "").lower()
            if any(key.lower() in content for key in expected_keys):
                return 1.0 / rank
        return 0.0
    
    def evaluate(self, result: Dict, test_case: Dict) -> Dict[str, Any]:
        retrieved_chunks = result.get("retrieved_chunks", [])
        expected_keys = test_case.get("expected_answer_keys", [])
        
        hit_rate = self.calculate_hit_rate(retrieved_chunks, expected_keys)
        mrr = self.calculate_mrr(retrieved_chunks, expected_keys)
        
        return {
            "hit_rate": hit_rate,
            "mrr": mrr,
            "num_chunks_retrieved": len(retrieved_chunks),
            "expected_keys": expected_keys,
            "keys_found": [k for k in expected_keys if any(k.lower() in c.get("content", "").lower() for c in retrieved_chunks)]
        }


if __name__ == "__main__":
    metrics = RetrievalMetrics()
    
    test_result = {
        "retrieved_chunks": [
            {"content": "复活节在春季第13天举行，地点是广场"},
            {"content": "参与复活节可以获得草莓种子"}
        ]
    }
    
    test_case = {
        "expected_answer_keys": ["春季", "13", "广场", "草莓种子"]
    }
    
    print(metrics.evaluate(test_result, test_case))
