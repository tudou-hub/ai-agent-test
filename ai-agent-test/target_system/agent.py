import json
import re
import os
import sys
from typing import Dict, List, Any, Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools import KnowledgeBase, TOOLS


class GameGuideAgent:
    def __init__(self, model_config: Dict = None, knowledge_dir: str = "target_system/knowledge"):
        self.kb = KnowledgeBase(knowledge_dir)
        self.tools = TOOLS
        self.conversation_history: List[Dict] = []
        self.system_prompt = """你是星露谷物语游戏攻略助手。你的任务是帮助玩家解决游戏中的问题。

你可以使用以下工具：
1. search_knowledge_base: 搜索攻略知识库
2. calculate_resource: 计算资源获取量
3. check_event_date: 查询节日活动

当玩家提问时，你应该：
- 如果问题涉及具体数值计算，使用calculate_resource
- 如果问题涉及节日活动，使用check_event_date
- 其他问题，使用search_knowledge_base搜索相关攻略

请用中文回答，保持友好和有帮助的态度。"""
    
    def _detect_intent(self, query: str) -> str:
        resource_keywords = ["金币", "gold", "木材", "wood", "石头", "stone", "纤维", "fiber", "资源", "赚钱", "收集"]
        cultivation_keywords = ["种植", "养殖", "升级", "技能", "等级", "经验", "养成", "农具"]
        event_keywords = ["节日", "活动", "复活节", "花舞节", "宴会", "万灵节", "冰雪节", "盛宴", "什么时候"]
        tool_keywords = ["工具", "怎么用", "如何使用", "操作", "方法"]
        
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in resource_keywords):
            return "resource"
        elif any(kw in query_lower for kw in cultivation_keywords):
            return "cultivation"
        elif any(kw in query_lower for kw in event_keywords):
            return "event"
        elif any(kw in query_lower for kw in tool_keywords):
            return "tool"
        return "general"
    
    def _should_use_tool(self, query: str, intent: str) -> Optional[str]:
        if intent == "resource" and any(kw in query for kw in ["多少", "计算", "能赚", "获得"]):
            return "calculate_resource"
        if intent == "event" and any(kw in query for kw in ["什么时候", "哪天", "日期", "时间"]):
            return "check_event_date"
        return "search_knowledge_base"
    
    def _extract_params(self, query: str, tool_name: str) -> Dict:
        if tool_name == "calculate_resource":
            resource_type = "gold"
            for r in ["金币", "gold", "钱"]:
                if r in query.lower():
                    resource_type = "gold"
                    break
                elif r in ["木材", "wood"]:
                    resource_type = "wood"
                    break
                elif r in ["石头", "stone"]:
                    resource_type = "stone"
                    break
            
            days = 7
            day_match = re.search(r'(\d+)\s*天', query)
            if day_match:
                days = int(day_match.group(1))
            
            return {"resource_type": resource_type, "days": days, "daily_yield": 0}
        
        elif tool_name == "check_event_date":
            events = ["复活节", "花舞节", "夏威夷宴会", "月光水母舞", "星露谷博览会", 
                     "万灵节", "冰雪节", "夜市", "冬日星盛宴"]
            for event in events:
                if event in query:
                    return {"event_name": event}
            return {"event_name": query.split("活动")[0].split("节")[0] + "节"}
        
        return {"query": query}
    
    def _call_tool(self, tool_name: str, params: Dict) -> Any:
        if tool_name not in self.tools:
            return {"error": f"未知工具: {tool_name}"}
        
        tool_info = self.tools[tool_name]
        func = tool_info["function"]
        
        try:
            if tool_name == "search_knowledge_base":
                return func(params.get("query", ""), self.kb)
            return func(**params)
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_response(self, query: str, tool_result: Any, intent: str) -> str:
        if isinstance(tool_result, dict):
            if "error" in tool_result:
                return f"抱歉，{tool_result['error']}"
            
            if "total_estimated" in tool_result:
                return f"根据计算，{tool_result['days']}天内预计可以获得约{tool_result['total_estimated']:.0f}{tool_result['resource_type']}。\n计算方式：{tool_result['formula']}"
            
            if "full_date" in tool_result:
                return f"{tool_result['event_name']}在{tool_result['full_date']}举行，地点是{tool_result['location']}。参与可获得{tool_result['reward']}。"
        
        if isinstance(tool_result, str):
            return f"根据攻略信息：\n{tool_result}\n\n希望对你有帮助！"
        
        return str(tool_result)
    
    def chat(self, query: str) -> Dict[str, Any]:
        intent = self._detect_intent(query)
        tool_name = self._should_use_tool(query, intent)
        params = self._extract_params(query, tool_name)
        
        tool_result = self._call_tool(tool_name, params)
        response = self._generate_response(query, tool_result, intent)
        
        result = {
            "query": query,
            "response": response,
            "intent": intent,
            "tool_called": tool_name,
            "tool_params": params,
            "tool_result": tool_result,
            "retrieved_chunks": []
        }
        
        if tool_name == "search_knowledge_base":
            result["retrieved_chunks"] = self.kb.search(params.get("query", query), top_k=3)
        
        self.conversation_history.append({
            "role": "user",
            "content": query
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return result
    
    def reset(self):
        self.conversation_history = []


if __name__ == "__main__":
    agent = GameGuideAgent()
    
    test_queries = [
        "复活节是什么时候？",
        "我想在7天内赚尽可能多的金币，怎么做？",
        "怎么种植蓝莓？"
    ]
    
    for q in test_queries:
        result = agent.chat(q)
        print(f"Q: {q}")
        print(f"Intent: {result['intent']}")
        print(f"Tool: {result['tool_called']}")
        print(f"A: {result['response']}")
        print("-" * 50)
