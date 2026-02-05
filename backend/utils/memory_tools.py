"""
Memory Management Tools for LLM Function Calling
"""
from typing import List, Dict, Any

MEMORY_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "记住用户提到的重要事实、偏好或背景信息，以便在未来的对话中参考。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "需要记住的具体信息内容，例如：'用户喜欢喝红茶' 或 '用户的生日是5月12日'。"
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "可选。如果这段记忆关联到特定的实体（人、地点、事物），可以指定实体名称。"
                    },
                    "importance": {
                        "type": "integer",
                        "description": "可选。记忆的重要性级别（1-10），默认为5。",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_memory",
            "description": "更新或修正之前记住的信息。当用户改变了主意或提供了更准确的信息时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "需要更新的记忆ID。你可以从之前的对话上下文或检索结果中获取此ID。"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "修正后的完整信息内容。"
                    }
                },
                "required": ["memory_id", "new_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_memory",
            "description": "当某条记忆已经过期、错误或用户明确要求忘记时，使用此工具删除记忆。",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "需要删除的记忆ID。"
                    },
                    "reason": {
                        "type": "string",
                        "description": "可选。为什么要删除这条记忆的原因。"
                    }
                },
                "required": ["memory_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memories",
            "description": "主动搜索特定的历史记忆或知识。当需要更精确地核实某个事实时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或语义查询。"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def get_memory_tools() -> List[Dict[str, Any]]:
    """获取所有记忆管理工具定义"""
    return MEMORY_TOOLS
