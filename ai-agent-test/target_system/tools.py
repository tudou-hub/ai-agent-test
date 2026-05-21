import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class KnowledgeBase:
    def __init__(self, knowledge_dir: str = "target_system/knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.chunks: List[str] = []
        self.metadata: List[Dict] = []
        self._load_knowledge()
    
    def _load_knowledge(self):
        for file_path in self.knowledge_dir.glob("*.txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                chunks = self._split_content(content, chunk_size=500)
                for i, chunk in enumerate(chunks):
                    self.chunks.append(chunk)
                    self.metadata.append({
                        "source": file_path.name,
                        "chunk_id": i
                    })
    
    def _split_content(self, content: str, chunk_size: int = 500) -> List[str]:
        paragraphs = content.split("\n\n")
        chunks = []
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        results = []
        query_keywords = set(query.lower().split())
        for i, chunk in enumerate(self.chunks):
            chunk_keywords = set(chunk.lower().split())
            overlap = len(query_keywords & chunk_keywords)
            if overlap > 0:
                results.append({
                    "content": chunk,
                    "metadata": self.metadata[i],
                    "score": overlap / len(query_keywords)
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def search_knowledge_base(query: str, kb: Optional[KnowledgeBase] = None) -> str:
    if kb is None:
        kb = KnowledgeBase()
    results = kb.search(query, top_k=3)
    if not results:
        return "未找到相关信息。"
    return "\n---\n".join([r["content"] for r in results])


def calculate_resource(resource_type: str, days: int, daily_yield: float = 0) -> Dict[str, Any]:
    calculations = {
        "gold": {"base": 50, "multiplier": 1.5},
        "wood": {"base": 20, "multiplier": 1.0},
        "stone": {"base": 15, "multiplier": 1.0},
        "fiber": {"base": 10, "multiplier": 1.2}
    }
    
    if resource_type.lower() not in calculations:
        return {"error": f"未知资源类型: {resource_type}"}
    
    config = calculations[resource_type.lower()]
    total = config["base"] * days * config["multiplier"] + daily_yield * days
    
    return {
        "resource_type": resource_type,
        "days": days,
        "daily_yield": daily_yield,
        "total_estimated": total,
        "formula": f"基础{config['base']}/天 × {days}天 × {config['multiplier']}倍率 + 额外{daily_yield}/天"
    }


def check_event_date(event_name: str) -> Dict[str, Any]:
    events = {
        "复活节": {"season": "春季", "day": 13, "location": "广场", "reward": "草莓种子"},
        "花舞节": {"season": "春季", "day": 24, "location": "煤矿森林", "reward": "舞蹈"},
        "夏威夷宴会": {"season": "夏季", "day": 11, "location": "海滩", "reward": "汤品评分"},
        "月光水母舞": {"season": "夏季", "day": 28, "location": "海滩", "reward": "水母"},
        "星露谷博览会": {"season": "秋季", "day": 16, "location": "广场", "reward": "星星代币"},
        "万灵节": {"season": "秋季", "day": 27, "location": "广场", "reward": "黄金南瓜"},
        "冰雪节": {"season": "冬季", "day": 8, "location": "森林", "reward": "钓鱼比赛"},
        "夜市": {"season": "冬季", "day": 15, "location": "海滩", "reward": "免费咖啡"},
        "冬日星盛宴": {"season": "冬季", "day": 25, "location": "广场", "reward": "神秘礼物"}
    }
    
    event_lower = event_name.lower().replace(" ", "")
    for name, info in events.items():
        if event_lower in name.lower().replace(" ", "") or name.lower().replace(" ", "") in event_lower:
            return {
                "event_name": name,
                **info,
                "full_date": f"{info['season']}第{info['day']}天"
            }
    
    return {"error": f"未找到活动: {event_name}", "available_events": list(events.keys())}


TOOLS = {
    "search_knowledge_base": {
        "function": search_knowledge_base,
        "description": "搜索游戏攻略知识库，获取相关攻略信息",
        "parameters": {
            "query": {"type": "string", "description": "搜索关键词或问题"}
        }
    },
    "calculate_resource": {
        "function": calculate_resource,
        "description": "计算资源获取量，支持gold/wood/stone/fiber",
        "parameters": {
            "resource_type": {"type": "string", "description": "资源类型"},
            "days": {"type": "integer", "description": "游戏天数"},
            "daily_yield": {"type": "float", "description": "每日额外产量", "default": 0}
        }
    },
    "check_event_date": {
        "function": check_event_date,
        "description": "查询游戏节日活动的日期和详情",
        "parameters": {
            "event_name": {"type": "string", "description": "活动名称"}
        }
    }
}
