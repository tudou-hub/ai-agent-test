from typing import List, Dict, Any
import re


class GenerationMetrics:
    def __init__(self):
        self.stopwords = set("的 是 在 有 和 了 不 这 那 么 什 么 怎 么 哪 谁".split())
    
    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'[\u4e00-\u9fff]+|[a-z0-9]+', text)
        return [t for t in tokens if t not in self.stopwords and len(t) > 1]
    
    def calculate_rouge_l(self, generated: str, reference: str) -> float:
        gen_tokens = self.tokenize(generated)
        ref_tokens = self.tokenize(reference)
        
        if not gen_tokens or not ref_tokens:
            return 0.0
        
        m = len(gen_tokens)
        n = len(ref_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if gen_tokens[i-1] == ref_tokens[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs = dp[m][n]
        precision = lcs / m if m > 0 else 0
        recall = lcs / n if n > 0 else 0
        
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)
    
    def calculate_key_coverage(self, response: str, expected_keys: List[str]) -> Dict[str, Any]:
        if not expected_keys:
            return {"coverage": 1.0, "found_keys": [], "missing_keys": []}
        
        response_lower = response.lower()
        found_keys = [k for k in expected_keys if k.lower() in response_lower]
        missing_keys = [k for k in expected_keys if k.lower() not in response_lower]
        
        coverage = len(found_keys) / len(expected_keys)
        
        return {
            "coverage": coverage,
            "found_keys": found_keys,
            "missing_keys": missing_keys
        }
    
    def detect_hallucination(self, response: str, retrieved_chunks: List[Dict], expected_keys: List[str]) -> Dict[str, Any]:
        if not retrieved_chunks:
            return {"hallucination_risk": "unknown", "reason": "无检索结果作为参考"}
        
        combined_knowledge = " ".join([c.get("content", "") for c in retrieved_chunks]).lower()
        response_lower = response.lower()
        
        numbers_in_response = re.findall(r'\d+', response)
        numbers_in_knowledge = re.findall(r'\d+', combined_knowledge)
        
        unverified_numbers = []
        for num in numbers_in_response:
            if num not in numbers_in_knowledge:
                unverified_numbers.append(num)
        
        key_coverage = self.calculate_key_coverage(response, expected_keys)
        
        if unverified_numbers and key_coverage["coverage"] < 0.5:
            risk = "high"
        elif unverified_numbers or key_coverage["coverage"] < 0.7:
            risk = "medium"
        else:
            risk = "low"
        
        return {
            "hallucination_risk": risk,
            "unverified_numbers": unverified_numbers,
            "key_coverage": key_coverage["coverage"]
        }
    
    def evaluate(self, result: Dict, test_case: Dict) -> Dict[str, Any]:
        response = result.get("response", "")
        expected_keys = test_case.get("expected_answer_keys", [])
        retrieved_chunks = result.get("retrieved_chunks", [])
        
        key_coverage = self.calculate_key_coverage(response, expected_keys)
        hallucination = self.detect_hallucination(response, retrieved_chunks, expected_keys)
        
        reference = " ".join(expected_keys)
        rouge_l = self.calculate_rouge_l(response, reference)
        
        return {
            "rouge_l": rouge_l,
            "key_coverage": key_coverage["coverage"],
            "found_keys": key_coverage["found_keys"],
            "missing_keys": key_coverage["missing_keys"],
            "hallucination_risk": hallucination["hallucination_risk"],
            "response_length": len(response)
        }


if __name__ == "__main__":
    metrics = GenerationMetrics()
    
    test_result = {
        "response": "复活节在春季第13天举行，地点是广场。参与可以获得草莓种子。",
        "retrieved_chunks": [
            {"content": "复活节在春季第13天举行"}
        ]
    }
    
    test_case = {
        "expected_answer_keys": ["春季", "13", "广场", "草莓种子"]
    }
    
    print(metrics.evaluate(test_result, test_case))
