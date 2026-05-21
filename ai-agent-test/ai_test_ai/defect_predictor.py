import json
import os
from typing import Dict, Any, List, Optional


class DefectPredictor:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        self.hallucination_indicators = [
            "具体数字但无来源",
            "超出知识库范围的细节",
            "与已知信息矛盾",
            "过度具体的描述"
        ]
        
        self.defect_types = {
            "hallucination": "幻觉 - 生成与事实不符的内容",
            "incomplete": "不完整 - 未覆盖关键信息",
            "irrelevant": "不相关 - 回答与问题无关",
            "refusal_error": "拒答错误 - 应回答但拒绝/应拒绝但回答",
            "tool_error": "工具错误 - 调用了错误的工具"
        }
    
    def predict_with_llm(self, query: str, response: str, knowledge: str = "") -> Dict[str, Any]:
        if not self.api_key:
            return self._rule_based_predict(query, response, knowledge)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""请分析以下AI回答是否存在缺陷。

问题：{query}
回答：{response}
参考知识：{knowledge if knowledge else "无"}

请判断：
1. 是否存在幻觉（编造不存在的信息）
2. 是否回答不完整
3. 是否与问题不相关
4. 是否应该拒答但回答了（或应该回答但拒绝了）

请以JSON格式输出：
{{
  "has_defect": true/false,
  "defect_types": ["hallucination/incomplete/irrelevant/refusal_error"],
  "confidence": 0.0-1.0,
  "reason": "判断理由",
  "suggestion": "改进建议"
}}"""
            
            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            result_text = completion.choices[0].message.content
            if "```" in result_text:
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            return json.loads(result_text)
        except Exception as e:
            return self._rule_based_predict(query, response, knowledge)
    
    def _rule_based_predict(self, query: str, response: str, knowledge: str) -> Dict[str, Any]:
        defects = []
        confidence = 0.5
        
        if knowledge:
            knowledge_lower = knowledge.lower()
            response_lower = response.lower()
            
            import re
            numbers_in_response = re.findall(r'\d+', response)
            numbers_in_knowledge = re.findall(r'\d+', knowledge)
            
            unverified = [n for n in numbers_in_response if n not in numbers_in_knowledge]
            if unverified and len(unverified) > 2:
                defects.append("hallucination")
                confidence += 0.2
        
        if len(response) < 20:
            defects.append("incomplete")
            confidence += 0.1
        
        refusal_words = ["抱歉", "无法", "不知道"]
        if any(w in response for w in refusal_words):
            defects.append("refusal_error")
        
        return {
            "has_defect": len(defects) > 0,
            "defect_types": defects,
            "confidence": min(confidence, 1.0),
            "reason": "基于规则的自动判断",
            "suggestion": "建议人工复核" if defects else "无明显缺陷"
        }
    
    def compare_with_human(self, ai_prediction: Dict, human_label: Dict) -> Dict[str, Any]:
        ai_defects = set(ai_prediction.get("defect_types", []))
        human_defects = set(human_label.get("defect_types", []))
        
        if not ai_defects and not human_defects:
            agreement = True
        elif ai_defects == human_defects:
            agreement = True
        else:
            agreement = len(ai_defects & human_defects) > 0
        
        return {
            "agreement": agreement,
            "ai_prediction": ai_defects,
            "human_label": human_defects,
            "precision": len(ai_defects & human_defects) / len(ai_defects) if ai_defects else 0,
            "recall": len(ai_defects & human_defects) / len(human_defects) if human_defects else 0
        }
    
    def batch_predict(self, results: List[Dict], test_cases: List[Dict]) -> List[Dict]:
        predictions = []
        
        for result, test_case in zip(results, test_cases):
            query = test_case.get("query", "")
            response = result.get("response", "")
            knowledge = " ".join([c.get("content", "") for c in result.get("retrieved_chunks", [])])
            
            prediction = self.predict_with_llm(query, response, knowledge)
            prediction["test_id"] = test_case.get("id", "unknown")
            predictions.append(prediction)
        
        return predictions


if __name__ == "__main__":
    predictor = DefectPredictor()
    
    result = {
        "response": "复活节在春季第13天举行，地点是广场。",
        "retrieved_chunks": [{"content": "复活节在春季第13天"}]
    }
    
    test_case = {
        "id": "test_001",
        "query": "复活节是什么时候？"
    }
    
    print(predictor.predict_with_llm(test_case["query"], result["response"]))
