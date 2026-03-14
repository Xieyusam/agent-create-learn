from typing import Annotated, Literal, TypedDict, List, Dict, Any
import yaml
import os
from dotenv import load_dotenv
from app.tools import (
    search_product,
    get_product_details,
    query_order_status,
    create_return_request,
    query_return_status,
    get_all_orders,
    get_all_products,
    update_user_preference
)
# ProductRAG will be resolved dynamically to avoid heavy imports at module import time
class ProductRAG: ...
from app.memory import memory_manager
class ChatOpenAI:
    def __init__(self, *args, **kwargs): ...
    def bind_tools(self, tools): return self
    def invoke(self, messages): return None


class AgentState(TypedDict):
    messages: List[Any]
    user_id: str
    current_intent: str
    context: str


class CustomerServiceAgent:
    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()
        path_from_env = os.getenv("APP_CONFIG_PATH") or config_path
        self.config = self._load_config(path_from_env)
        self._validate_config(self.config)
        self.llm = self._init_llm()
        try:
            from app.rag import ProductRAG as RealProductRAG  # type: ignore
            rag_cls = RealProductRAG
        except Exception:
            rag_cls = ProductRAG
        self.rag = rag_cls()
        self.tools = [
            search_product,
            get_product_details,
            query_order_status,
            create_return_request,
            query_return_status,
            get_all_orders,
            get_all_products,
            update_user_preference
        ]
        self.tool_node = None
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.graph = self._build_graph()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            content = os.path.expandvars(content)
            return yaml.safe_load(content)
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("配置文件格式错误")
        current = config.get("current_model")
        models = config.get("models") or {}
        if not current or current not in models:
            raise ValueError("配置缺失或未定义的 current_model")
        mc = models.get(current) or {}
        api_key = str(mc.get("api_key") or "").strip()
        model = str(mc.get("model") or "").strip()
        base_url = str(mc.get("base_url") or "").strip()
        placeholders = {"", "your-api-key", "your_api_key_here", "your-api-key-here", "replace-me", "changeme"}
        if api_key in placeholders or api_key.startswith("${"):
            raise ValueError("缺少必须的环境变量或 api_key 未设置")
        if not model:
            raise ValueError("模型配置缺少 model")
        if not base_url:
            raise ValueError("模型配置缺少 base_url")
    
    def _init_llm(self):
        global ChatOpenAI
        try:
            from langchain_openai import ChatOpenAI as RealChatOpenAI  # type: ignore
            ChatOpenAI = RealChatOpenAI
        except Exception:
            pass
        model_config = self.config["models"][self.config["current_model"]]
        return ChatOpenAI(
            api_key=model_config["api_key"],
            model=model_config["model"],
            base_url=model_config["base_url"],
            temperature=model_config.get("temperature", 0.1)
        )
    
    def _get_system_prompt(self) -> str:
        return """你是一个专业、友好、高效的电商客服助手。你的职责是帮助用户解决各种问题，包括产品咨询、订单查询、退换货处理等。

你的工作原则：
1. 友好礼貌：始终保持友好和专业的态度
2. 准确高效：提供准确的信息，快速响应用户需求
3. 主动帮助：主动询问用户是否需要其他帮助
4. 保护隐私：不询问或泄露用户的敏感信息
5. 记忆偏好：主动记录用户的偏好和重要信息，以便提供个性化服务

你可以使用以下工具来帮助用户：
- search_product: 搜索产品信息
- get_product_details: 获取产品详细信息
- query_order_status: 查询订单状态和物流信息
- create_return_request: 创建退换货申请
- query_return_status: 查询退换货申请状态
- get_all_orders: 获取用户的所有订单
- get_all_products: 获取所有产品列表
- update_user_preference: 更新用户偏好或画像信息

当用户询问产品相关问题时，你可以先使用RAG检索相关的产品知识库信息，然后结合工具调用提供更全面的回答。
当用户表达特定的偏好、需求或重要信息时，请调用 update_user_preference 工具进行记录。

请根据用户的问题，选择合适的工具来获取信息，然后用自然、友好的语言回答用户。如果不需要调用工具，直接回答用户即可。"""
    
    def _should_continue(self, state: AgentState) -> Literal["tools", "__end__"]:
        messages = state["messages"]
        last_message = messages[-1]
        if getattr(last_message, "tool_calls", None):
            return "tools"
        return "__end__"
    
    def _call_model(self, state: AgentState) -> Dict[str, Any]:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = state["messages"]
        user_id = state.get("user_id", "U001")
        last_human_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_human_message = msg.content
                break
        context = ""
        if last_human_message:
            context = self.rag.get_context(last_human_message)
        user_profile = memory_manager.get_user_profile(user_id)
        base_prompt = self._get_system_prompt()
        if user_profile:
            base_prompt += f"\n\n【用户画像/偏好信息】\n{user_profile}"
        system_message = SystemMessage(content=base_prompt)
        if context:
            system_message_content = f"""{base_prompt}

以下是相关的产品知识库信息，供你参考：
{context}"""
            system_message = SystemMessage(content=system_message_content)
        response = self.llm_with_tools.invoke([system_message] + messages)
        return {"messages": [response]}
    
    def _build_graph(self):
        try:
            from langgraph.graph import StateGraph, START, END
            from langgraph.prebuilt import ToolNode
            self.tool_node = ToolNode(self.tools)
            workflow = StateGraph(AgentState)
            workflow.add_node("agent", self._call_model)
            workflow.add_node("tools", self.tool_node)
            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "tools": "tools",
                    END: END
                }
            )
            workflow.add_edge("tools", "agent")
            return workflow.compile()
        except Exception:
            class _Graph:
                def invoke(self, state): return {"messages": []}
                def stream(self, state): 
                    if False:
                        yield {}
            return _Graph()
    
    def chat(self, user_input: str, user_id: str = "U001", history: List[Any] = None) -> Dict[str, Any]:
        from langchain_core.messages import HumanMessage, AIMessage
        if history is None:
            history = []
        history.append(HumanMessage(content=user_input))
        initial_state = {
            "messages": history,
            "user_id": user_id,
            "current_intent": "",
            "context": ""
        }
        result = self.graph.invoke(initial_state)
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        last_ai_message = ai_messages[-1] if ai_messages else AIMessage(content="抱歉，我无法处理您的请求。")
        return {
            "response": last_ai_message.content,
            "history": result["messages"],
            "tool_calls": last_ai_message.tool_calls if hasattr(last_ai_message, 'tool_calls') else []
        }
    
    def stream_chat(self, user_input: str, user_id: str = "U001", history: List[Any] = None):
        from langchain_core.messages import HumanMessage, AIMessage
        if history is None:
            history = []
        history.append(HumanMessage(content=user_input))
        initial_state = {
            "messages": history,
            "user_id": user_id,
            "current_intent": "",
            "context": ""
        }
        for output in self.graph.stream(initial_state):
            for key, value in output.items():
                if key == "agent" and "messages" in value:
                    msg = value["messages"][0]
                    if isinstance(msg, AIMessage) and msg.content:
                        yield msg.content
