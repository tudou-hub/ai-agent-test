from typing import Dict, Any


class IntentMetrics:
    def __init__(self):
        self.valid_intents = ["resource", "cultivation", "event", "tool", "general"]
        self.confusion_matrix = {intent: {i: 0 for i in self.valid_intents} for intent in self.valid_intents}
    
    def evaluate_single(self, predicted_intent: str, true_intent: str) -> Dict[str, Any]:
        is_correct = predicted_intent == true_intent
        
        if predicted_intent in self.valid_intents and true_intent in self.valid_intents:
            self.confusion_matrix[true_intent][predicted_intent] += 1
        
        return {
            "predicted": predicted_intent,
            "true": true_intent,
            "correct": is_correct
        }
    
    def get_overall_metrics(self) -> Dict[str, Any]:
        total = sum(sum(row.values()) for row in self.confusion_matrix.values())
        if total == 0:
            return {"accuracy": 0, "per_intent_accuracy": {}}
        
        correct = sum(self.confusion_matrix[i][i] for i in self.valid_intents)
        accuracy = correct / total
        
        per_intent = {}
        for intent in self.valid_intents:
            intent_total = sum(self.confusion_matrix[intent].values())
            if intent_total > 0:
                per_intent[intent] = self.confusion_matrix[intent][intent] / intent_total
            else:
                per_intent[intent] = 0
        
        return {
            "accuracy": accuracy,
            "per_intent_accuracy": per_intent,
            "confusion_matrix": self.confusion_matrix
        }
    
    def reset(self):
        self.confusion_matrix = {intent: {i: 0 for i in self.valid_intents} for intent in self.valid_intents}
    
    def evaluate(self, result: Dict, test_case: Dict) -> Dict[str, Any]:
        predicted = result.get("intent", "general")
        true_intent = test_case.get("intent", "general")
        
        single_result = self.evaluate_single(predicted, true_intent)
        
        return {
            "intent_accuracy": 1.0 if single_result["correct"] else 0.0,
            "predicted_intent": predicted,
            "true_intent": true_intent,
            "correct": single_result["correct"]
        }


if __name__ == "__main__":
    metrics = IntentMetrics()
    
    test_result = {"intent": "event"}
    test_case = {"intent": "event"}
    
    print(metrics.evaluate(test_result, test_case))
    
    test_result2 = {"intent": "resource"}
    test_case2 = {"intent": "event"}
    
    print(metrics.evaluate(test_result2, test_case2))
    
    print(metrics.get_overall_metrics())
