from typing import Dict, Any, List
from datetime import datetime
import json
import os


class ReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(self, results: List[Dict], summary: Dict, config: Dict = None) -> Dict[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        md_report = self._generate_markdown(results, summary, config)
        json_report = self._generate_json(results, summary, config)
        
        md_path = os.path.join(self.output_dir, f"benchmark_report_{timestamp}.md")
        json_path = os.path.join(self.output_dir, f"benchmark_report_{timestamp}.json")
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_report)
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        return {"markdown": md_path, "json": json_path}
    
    def _generate_markdown(self, results: List[Dict], summary: Dict, config: Dict) -> str:
        lines = []
        
        lines.append("# AI Agent Benchmark 评测报告")
        lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")
        
        lines.append("## 1. 总体概览\n")
        
        total_cases = sum(s.get("count", 0) for s in summary.values())
        lines.append(f"- **测试用例总数**：{total_cases}")
        lines.append(f"- **测试类别**：{', '.join(summary.keys())}")
        
        all_scores = [s.get("avg_overall_score", 0) for s in summary.values()]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        lines.append(f"- **平均综合得分**：{avg_score:.3f}")
        
        lines.append("\n## 2. 分类指标详情\n")
        
        for category, metrics in summary.items():
            lines.append(f"### {category}\n")
            lines.append(f"| 指标 | 数值 |")
            lines.append(f"|------|------|")
            lines.append(f"| 用例数量 | {metrics.get('count', 0)} |")
            lines.append(f"| 平均得分 | {metrics.get('avg_overall_score', 0):.3f} |")
            
            if "avg_retrieval_hit_rate" in metrics:
                lines.append(f"| 检索命中率 | {metrics.get('avg_retrieval_hit_rate', 0):.3f} |")
            if "avg_generation_coverage" in metrics:
                lines.append(f"| 答案覆盖率 | {metrics.get('avg_generation_coverage', 0):.3f} |")
            if "intent_accuracy" in metrics:
                lines.append(f"| 意图识别准确率 | {metrics.get('intent_accuracy', 0):.3f} |")
            if "tool_selection_accuracy" in metrics:
                lines.append(f"| 工具选择准确率 | {metrics.get('tool_selection_accuracy', 0):.3f} |")
            if "attack_success_rate" in metrics:
                lines.append(f"| 攻击成功率 | {metrics.get('attack_success_rate', 0):.3f} |")
            if "defense_success_rate" in metrics:
                lines.append(f"| 防御成功率 | {metrics.get('defense_success_rate', 0):.3f} |")
            lines.append("")
        
        lines.append("## 3. 失败案例分析\n")
        
        failed_cases = [r for r in results if r.get("overall", {}).get("score", 1) < 0.5]
        
        if failed_cases:
            lines.append(f"共 {len(failed_cases)} 个失败案例：\n")
            for i, case in enumerate(failed_cases[:10], 1):
                lines.append(f"### 案例 {i}\n")
                lines.append(f"- **ID**：{case.get('test_id', 'unknown')}")
                lines.append(f"- **问题**：{case.get('query', '')}")
                lines.append(f"- **得分**：{case.get('overall', {}).get('score', 0):.3f}")
                lines.append(f"- **回答**：{case.get('response', '')[:200]}...")
                lines.append("")
        else:
            lines.append("无失败案例。\n")
        
        lines.append("## 4. JD指标映射\n")
        lines.append("| JD要求 | 对应指标 | 得分 |")
        lines.append("|--------|----------|------|")
        
        jd_mapping = [
            ("准确率", "avg_generation_coverage", "generation"),
            ("召回率", "avg_retrieval_hit_rate", "retrieval"),
            ("幻觉率", "hallucination_rate", "generation"),
            ("意图识别率", "intent_accuracy", "intent"),
            ("工具调用", "tool_selection_accuracy", "agent"),
            ("安全压测", "defense_success_rate", "security")
        ]
        
        for jd_name, metric_name, category in jd_mapping:
            if category in summary and metric_name in summary[category]:
                score = summary[category].get(metric_name, 0)
                lines.append(f"| {jd_name} | {metric_name} | {score:.3f} |")
        
        lines.append("\n---\n")
        lines.append("*报告由 AI Agent Benchmark 系统自动生成*")
        
        return "\n".join(lines)
    
    def _generate_json(self, results: List[Dict], summary: Dict, config: Dict) -> Dict:
        return {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "total_cases": len(results),
                "config": config
            },
            "summary": summary,
            "detailed_results": results
        }


if __name__ == "__main__":
    generator = ReportGenerator()
    
    test_results = [
        {
            "test_id": "basic_001",
            "query": "复活节是什么时候？",
            "category": "basic",
            "response": "复活节在春季第13天举行。",
            "overall": {"score": 0.85}
        }
    ]
    
    test_summary = {
        "basic": {
            "count": 1,
            "avg_overall_score": 0.85,
            "avg_retrieval_hit_rate": 0.9,
            "avg_generation_coverage": 0.8
        }
    }
    
    print(generator.generate(test_results, test_summary))
