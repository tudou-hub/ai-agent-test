from typing import Dict, Any, List


class AgentMetrics:
    def __init__(self):
        self.results = []
    
    def evaluate_tool_selection(self, tool_called: str, expected_tool: str) -> Dict[str, Any]:
        if expected_tool is None:
            correct = tool_called is None or tool_called == "search_knowledge_base"
        else:
            correct = tool_called == expected_tool
        
        return {
            "correct": correct,
            "tool_called": tool_called,
            "expected_tool": expected_tool
        }
    
    def evaluate_task_completion(self, response: str, expected_keys: List[str], should_answer: bool) -> Dict[str, Any]:
        if not should_answer:
            refused = self._check_refusal(response)
            return {
                "correct_behavior": refused,
                "refused": refused,
                "should_answer": False
            }
        
        found_keys = [k for k in expected_keys if k.lower() in response.lower()]
        completion_rate = len(found_keys) / len(expected_keys) if expected_keys else 1.0
        
        return {
            "completion_rate": completion_rate,
            "found_keys": found_keys,
            "missing_keys": [k for k in expected_keys if k not in found_keys],
            "should_answer": True
        }
    
    def _check_refusal(self, response: str) -> bool:
        refusal_patterns = [
            "抱歉", "无法", "不知道", "不清楚", "没有相关",
            "无法回答", "不能回答", "不在我", "超出"
        ]
        response_lower = response.lower()
        return any(p in response_lower for p in refusal_patterns)
    
    def evaluate_decision_rationality(self, result: Dict, test_case: Dict) -> Dict[str, Any]:
        issues = []
        tool_called = result.get("tool_called")
        response = result.get("response", "")
        
        if tool_called and "error" in str(result.get("tool_result", "")):
            issues.append("工具调用失败")
        
        if len(response) < 10:
            issues.append("回复过短")
        
        if tool_called == "calculate_resource":
            tool_result = result.get("tool_result", {})
            if isinstance(tool_result, dict) and "error" not in tool_result:
                if tool_result.get("total_estimated", 0) <= 0:
                    issues.append("计算结果异常")
        
        return {
            "rational": len(issues) == 0,
            "issues": issues,
            "tool_called": tool_called
        }
    
    def evaluate(self, result: Dict, test_case: Dict) -> Dict[str, Any]:
        tool_called = result.get("tool_called")
        expected_tool = test_case.get("expected_tool")
        expected_keys = test_case.get("expected_answer_keys", [])
        should_answer = test_case.get("should_answer", True)
        response = result.get("response", "")
        
        tool_selection = self.evaluate_tool_selection(tool_called, expected_tool)
        task_completion = self.evaluate_task_completion(response, expected_keys, should_answer)
        decision = self.evaluate_decision_rationality(result, test_case)
        
        return {
            "tool_selection_correct": tool_selection["correct"],
            "tool_called": tool_called,
            "expected_tool": expected_tool,
            "task_completion_rate": task_completion.get("completion_rate", 0),
            "decision_rational": decision["rational"],
            "decision_issues": decision["issues"]
        }


if __name__ == "__main__":
    metrics = AgentMetrics()
    
    test_result = {
        "tool_called": "check_event_date",
        "response": "复活节在春季第13天举行，地点是广场。",
        "tool_result": {"event_name": "复活节", "season": "春季", "day": 13}
    }
    
    test_case = {
        "expected_tool": "check_event_date",
        "expected_answer_keys": ["春季", "13", "广场"],
        "should_answer": True
    }
    
    print(metrics.evaluate(test_result, test_case))
