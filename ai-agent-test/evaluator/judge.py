from typing import Dict, Any, List, Optional
import json
import os


class LLMJudge:
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.judge_prompt_template = """你是一个专业的AI回答质量评估专家。请评估以下回答的质量。

问题：{query}
回答：{response}
期望包含的关键信息：{expected_keys}

请从以下维度打分（0-10分）：
1. 准确性：回答中的信息是否准确
2. 完整性：是否覆盖了期望的关键信息
3. 相关性：回答是否与问题相关
4. 流畅性：回答是否通顺易懂

请以JSON格式输出：
{{
    "accuracy": <分数>,
    "completeness": <分数>,
    "relevance": <分数>,
    "fluency": <分数>,
    "hallucination_detected": <true/false>,
    "hallucination_reason": "<如果有幻觉，说明原因>",
    "overall_score": <综合分数>,
    "comment": "<简短评价>"
}}"""
    
    def build_judge_prompt(self, query: str, response: str, expected_keys: List[str]) -> str:
        return self.judge_prompt_template.format(
            query=query,
            response=response,
            expected_keys=", ".join(expected_keys) if expected_keys else "无特定期望"
        )
    
    def judge_with_llm(self, query: str, response: str, expected_keys: List[str]) -> Dict[str, Any]:
        if not self.api_key:
            return self._mock_judge(query, response, expected_keys)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = self.build_judge_prompt(query, response, expected_keys)
            
            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            result_text = completion.choices[0].message.content
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            return json.loads(result_text)
        except Exception as e:
            return self._mock_judge(query, response, expected_keys, error=str(e))
    
    def _mock_judge(self, query: str, response: str, expected_keys: List[str], error: str = None) -> Dict[str, Any]:
        response_lower = response.lower()
        
        found_keys = sum(1 for k in expected_keys if k.lower() in response_lower)
        completeness = found_keys / len(expected_keys) if expected_keys else 1.0
        
        accuracy = min(10, completeness * 10 + 2)
        relevance = 9 if any(k.lower() in response_lower for k in expected_keys) else 5
        fluency = 8 if len(response) > 20 else 5
        
        return {
            "accuracy": round(accuracy, 1),
            "completeness": round(completeness * 10, 1),
            "relevance": relevance,
            "fluency": fluency,
            "hallucination_detected": False,
            "hallucination_reason": None,
            "overall_score": round((accuracy + completeness * 10 + relevance + fluency) / 4, 1),
            "comment": f"自动评估（Mock模式）" + (f"，错误：{error}" if error else "")
        }
    
    def evaluate(self, result: Dict, test_case: Dict) -> Dict[str, Any]:
        query = test_case.get("query", "")
        response = result.get("response", "")
        expected_keys = test_case.get("expected_answer_keys", [])
        
        judge_result = self.judge_with_llm(query, response, expected_keys)
        
        return {
            "judge_scores": judge_result,
            "query": query,
            "response_length": len(response)
        }
    
    def consistency_check(self, result1: Dict, result2: Dict) -> float:
        score1 = result1.get("overall_score", 0)
        score2 = result2.get("overall_score", 0)
        
        diff = abs(score1 - score2)
        consistency = 1 - (diff / 10)
        
        return consistency


if __name__ == "__main__":
    judge = LLMJudge()
    
    test_result = {
        "response": "复活节在春季第13天举行，地点是广场。参与可以获得草莓种子。"
    }
    
    test_case = {
        "query": "复活节是什么时候？",
        "expected_answer_keys": ["春季", "13", "广场", "草莓种子"]
    }
    
    print(judge.evaluate(test_result, test_case))
