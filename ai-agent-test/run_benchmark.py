import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from target_system.agent import GameGuideAgent
from evaluator.scorer import Scorer
from evaluator.report import ReportGenerator
from ai_test_ai.case_generator import TestCaseGenerator
from ai_test_ai.defect_predictor import DefectPredictor


def load_test_data(data_dir: str = None) -> list:
    all_cases = []
    json_files = [
        "basic_qa.json",
        "intent_test.json",
        "edge_cases.json",
        "no_answer.json",
        "time_sensitive.json",
        "security_test.json"
    ]
    
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
    
    for filename in json_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                cases = json.load(f)
                all_cases.extend(cases)
                print(f"Loaded {len(cases)} cases from {filename}")
        else:
            print(f"Warning: File not found - {filepath}")
    
    return all_cases


def run_benchmark(agent: GameGuideAgent, test_cases: list, scorer: Scorer) -> list:
    results = []
    
    for i, case in enumerate(test_cases):
        print(f"Processing [{i+1}/{len(test_cases)}]: {case.get('id', 'unknown')}")
        
        result = agent.chat(case["query"])
        
        scores = scorer.score_single(result, case)
        
        combined = {
            "test_id": case.get("id", "unknown"),
            "query": case.get("query", ""),
            "category": case.get("category", "unknown"),
            "response": result.get("response", ""),
            "intent": result.get("intent", ""),
            "tool_called": result.get("tool_called", ""),
            "expected_tool": case.get("expected_tool"),
            "expected_answer_keys": case.get("expected_answer_keys", []),
            **scores
        }
        
        results.append(combined)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="AI Agent Benchmark Runner")
    parser.add_argument("--data-dir", default=None, help="Test data directory")
    parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    parser.add_argument("--generate-cases", action="store_true", help="Generate additional test cases")
    parser.add_argument("--num-generated", type=int, default=10, help="Number of cases to generate")
    parser.add_argument("--defect-prediction", action="store_true", help="Run AI defect prediction")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI Agent Benchmark System")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("[1/4] Loading test data...")
    test_cases = load_test_data(args.data_dir)
    print(f"Total test cases: {len(test_cases)}")
    print()
    
    if args.generate_cases:
        print("[1.5/4] Generating additional test cases...")
        generator = TestCaseGenerator()
        new_cases = generator.generate_with_llm([], num_cases=args.num_generated)
        test_cases.extend(new_cases)
        print(f"Generated {len(new_cases)} new cases")
        print()
    
    print("[2/4] Initializing agent and scorer...")
    agent = GameGuideAgent()
    scorer = Scorer()
    print("Agent and scorer initialized.")
    print()
    
    print("[3/4] Running benchmark...")
    results = run_benchmark(agent, test_cases, scorer)
    print(f"Benchmark completed. {len(results)} cases processed.")
    print()
    
    if args.defect_prediction:
        print("[3.5/4] Running AI defect prediction...")
        predictor = DefectPredictor()
        predictions = predictor.batch_predict(results, test_cases)
        for i, result in enumerate(results):
            result["ai_defect_prediction"] = predictions[i]
        print("Defect prediction completed.")
        print()
    
    print("[4/4] Generating report...")
    summary = scorer.aggregate_results(results)
    
    report_gen = ReportGenerator(output_dir=args.output_dir)
    report_paths = report_gen.generate(results, summary)
    
    print(f"Report saved to:")
    print(f"  - Markdown: {report_paths['markdown']}")
    print(f"  - JSON: {report_paths['json']}")
    print()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for category, metrics in summary.items():
        print(f"\n[{category.upper()}]")
        print(f"  Count: {metrics.get('count', 0)}")
        print(f"  Avg Score: {metrics.get('avg_overall_score', 0):.3f}")
        if "intent_accuracy" in metrics:
            print(f"  Intent Accuracy: {metrics.get('intent_accuracy', 0):.3f}")
        if "tool_selection_accuracy" in metrics:
            print(f"  Tool Selection: {metrics.get('tool_selection_accuracy', 0):.3f}")
        if "attack_success_rate" in metrics:
            print(f"  Attack Success Rate: {metrics.get('attack_success_rate', 0):.3f}")
            print(f"  Defense Success Rate: {metrics.get('defense_success_rate', 0):.3f}")
    
    print()
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return results, summary


if __name__ == "__main__":
    main()
