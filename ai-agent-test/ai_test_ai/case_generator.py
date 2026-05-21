import json
import os
from typing import List, Dict, Any, Optional
import random


class TestCaseGenerator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        self.templates = {
            "basic": [
                "{entity}是什么时候？",
                "{entity}怎么获得？",
                "{entity}有什么用？",
                "怎么{action}？",
                "{entity}在哪？"
            ],
            "edge": [
                "那个{attribute}的{entity}",
                "我想{goal}，怎么办？",
                "{entity}和{entity2}哪个更好？",
                "如果{condition}，会怎么样？"
            ],
            "no_answer": [
                "明天的{irrelevant}怎么样？",
                "游戏里怎么{impossible_action}？"
            ]
        }
        
        self.entities = [
            "复活节", "花舞节", "夏威夷宴会", "星露谷博览会",
            "蓝莓", "草莓", "南瓜", "鱼", "矿洞",
            "金币", "木材", "石头"
        ]
        
        self.actions = [
            "种植", "养殖", "钓鱼", "挖矿", "升级"
        ]
    
    def generate_with_llm(self, knowledge_chunks: List[str], num_cases: int = 10) -> List[Dict]:
        if not self.api_key:
            return self._generate_template_based(num_cases)
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""基于以下游戏攻略知识，生成{num_cases}个测试问题。
要求覆盖不同类型：基础问题、边界问题、无答案问题。

知识内容：
{chr(10).join(knowledge_chunks[:5])}

请以JSON格式输出：
[
  {{
    "query": "问题内容",
    "category": "basic/edge/no_answer",
    "intent": "resource/cultivation/event/tool/general",
    "expected_answer_keys": ["关键信息1", "关键信息2"],
    "should_answer": true/false
  }}
]"""
            
            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            result_text = completion.choices[0].message.content
            if "```" in result_text:
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            return json.loads(result_text)
        except Exception as e:
            return self._generate_template_based(num_cases)
    
    def _generate_template_based(self, num_cases: int) -> List[Dict]:
        cases = []
        
        for i in range(num_cases):
            category = random.choice(["basic", "edge", "no_answer"])
            template = random.choice(self.templates[category])
            entity = random.choice(self.entities)
            action = random.choice(self.actions)
            
            query = template.format(
                entity=entity,
                action=action,
                attribute=random.choice(["春天", "夏天", "红色", "大的"]),
                goal=random.choice(["赚钱", "升级", "收集"]),
                entity2=random.choice(self.entities),
                condition="下雨",
                irrelevant=random.choice(["天气", "股票", "彩票"]),
                impossible_action=random.choice(["坐飞机", "炒股", "买彩票"])
            )
            
            intent = "event" if category == "basic" and "什么时候" in query else \
                     "resource" if "怎么获得" in query or "金币" in query else \
                     "cultivation" if "种植" in query or "养殖" in query else "general"
            
            cases.append({
                "id": f"generated_{i+1:03d}",
                "query": query,
                "category": category,
                "intent": intent,
                "expected_answer_keys": [],
                "should_answer": category != "no_answer",
                "difficulty": "medium",
                "notes": "AI自动生成，需人工审核"
            })
        
        return cases
    
    def save_generated_cases(self, cases: List[Dict], output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        print(f"已生成 {len(cases)} 条测试用例到 {output_path}")


if __name__ == "__main__":
    generator = TestCaseGenerator()
    cases = generator.generate_with_llm([], num_cases=10)
    for case in cases:
        print(f"[{case['category']}] {case['query']}")
