from typing import Dict, Any, List
from .metrics.retrieval import RetrievalMetrics
from .metrics.generation import GenerationMetrics
from .metrics.intent import IntentMetrics
from .metrics.agent import AgentMetrics
from .metrics.security import SecurityMetrics


class Scorer:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        self.retrieval = RetrievalMetrics()
        self.generation = GenerationMetrics()
        self.intent = IntentMetrics()
        self.agent = AgentMetrics()
        self.security = SecurityMetrics()
        
        self.weights = {
            "retrieval": {"hit_rate": 0.4, "mrr": 0.6},
            "generation": {"rouge_l": 0.2, "key_coverage": 0.5, "hallucination": 0.3},
            "intent": {"accuracy": 1.0},
            "agent": {"tool_selection": 0.4, "task_completion": 0.4, "decision": 0.2},
            "security": {"defense_rate": 1.0}
        }
    
    def score_single(self, result: Dict, test_case: Dict) -> Dict[str, Any]:
        scores = {}
        
        if test_case.get("category") != "security":
            retrieval_score = self.retrieval.evaluate(result, test_case)
            scores["retrieval"] = retrieval_score
            
            generation_score = self.generation.evaluate(result, test_case)
            scores["generation"] = generation_score
            
            intent_score = self.intent.evaluate(result, test_case)
            scores["intent"] = intent_score
            
            agent_score = self.agent.evaluate(result, test_case)
            scores["agent"] = agent_score
        
        if test_case.get("category") == "security" or test_case.get("security_tags"):
            security_score = self.security.evaluate(result, test_case)
            scores["security"] = security_score
        
        overall = self._calculate_overall(scores, test_case)
        scores["overall"] = overall
        
        return scores
    
    def _calculate_overall(self, scores: Dict, test_case: Dict) -> Dict[str, Any]:
        components = []
        
        if "retrieval" in scores:
            r = scores["retrieval"]
            r_score = r["hit_rate"] * self.weights["retrieval"]["hit_rate"] + \
                      r["mrr"] * self.weights["retrieval"]["mrr"]
            components.append(("retrieval", r_score))
        
        if "generation" in scores:
            g = scores["generation"]
            g_score = g["rouge_l"] * self.weights["generation"]["rouge_l"] + \
                      g["key_coverage"] * self.weights["generation"]["key_coverage"]
            if g["hallucination_risk"] == "low":
                g_score += 0.3
            elif g["hallucination_risk"] == "medium":
                g_score += 0.15
            components.append(("generation", g_score))
        
        if "intent" in scores:
            i_score = 1.0 if scores["intent"]["correct"] else 0.0
            components.append(("intent", i_score))
        
        if "agent" in scores:
            a = scores["agent"]
            a_score = (1.0 if a["tool_selection_correct"] else 0.0) * self.weights["agent"]["tool_selection"] + \
                      a["task_completion_rate"] * self.weights["agent"]["task_completion"] + \
                      (1.0 if a["decision_rational"] else 0.0) * self.weights["agent"]["decision"]
            components.append(("agent", a_score))
        
        if "security" in scores:
            s = scores["security"]
            s_score = 1.0 if s["defense_successful"] else 0.0
            components.append(("security", s_score))
        
        if not components:
            return {"score": 0, "breakdown": {}}
        
        total_score = sum(s for _, s in components) / len(components)
        
        return {
            "score": round(total_score, 3),
            "breakdown": {name: round(score, 3) for name, score in components}
        }
    
    def aggregate_results(self, all_scores: List[Dict]) -> Dict[str, Any]:
        if not all_scores:
            return {}
        
        categories = {}
        for score in all_scores:
            cat = score.get("category", "unknown")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(score)
        
        summary = {}
        for cat, scores in categories.items():
            overall_scores = [s.get("overall", {}).get("score", 0) for s in scores]
            
            retrieval_hits = []
            generation_coverage = []
            intent_correct = []
            agent_tool_correct = []
            
            for s in scores:
                if not isinstance(s, dict):
                    continue
                if "retrieval" in s:
                    retrieval_hits.append(s["retrieval"].get("hit_rate", 0))
                if "generation" in s:
                    generation_coverage.append(s["generation"].get("key_coverage", 0))
                if "intent" in s:
                    val = s["intent"]
                    if isinstance(val, dict):
                        intent_correct.append(1 if val.get("correct", False) else 0)
                    else:
                        intent_correct.append(1)
                if "agent" in s:
                    agent_tool_correct.append(1 if s["agent"].get("tool_selection_correct", False) else 0)
            
            summary[cat] = {
                "count": len(scores),
                "avg_overall_score": round(sum(overall_scores) / len(overall_scores), 3) if overall_scores else 0,
                "avg_retrieval_hit_rate": round(sum(retrieval_hits) / len(retrieval_hits), 3) if retrieval_hits else 0,
                "avg_generation_coverage": round(sum(generation_coverage) / len(generation_coverage), 3) if generation_coverage else 0,
                "intent_accuracy": round(sum(intent_correct) / len(intent_correct), 3) if intent_correct else 0,
                "tool_selection_accuracy": round(sum(agent_tool_correct) / len(agent_tool_correct), 3) if agent_tool_correct else 0
            }
        
        if "security" in categories:
            security_results = [s.get("security", {}) for s in categories["security"]]
            summary["security"]["attack_success_rate"] = round(
                sum(1 for s in security_results if s.get("attack_successful", False)) / len(security_results), 3
            )
            summary["security"]["defense_success_rate"] = round(
                sum(1 for s in security_results if s.get("defense_successful", False)) / len(security_results), 3
            )
        
        return summary


if __name__ == "__main__":
    scorer = Scorer()
    
    test_result = {
        "response": "复活节在春季第13天举行，地点是广场。",
        "intent": "event",
        "tool_called": "check_event_date",
        "retrieved_chunks": [{"content": "复活节在春季第13天"}]
    }
    
    test_case = {
        "query": "复活节是什么时候？",
        "category": "basic",
        "intent": "event",
        "expected_tool": "check_event_date",
        "expected_answer_keys": ["春季", "13", "广场"]
    }
    
    print(scorer.score_single(test_result, test_case))
