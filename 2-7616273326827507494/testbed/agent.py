from typing import Annotated, Literal, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from config import load_config
from tools import tools
from rag import product_rag


# 定义状态类型
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    context: Optional[str]


# 系统提示词
SYSTEM_PROMPT = """你是一个专业的电商智能客服助手，名为"小智"。你的职责是帮助用户解决关于产品咨询、订单查询、物流跟踪和退换货申请等问题。

你的特点：
1. 友好、专业、耐心
2. 能够准确理解用户的需求
3. 善于使用工具获取准确信息
4. 提供清晰、有条理的回答

工作流程：
1. 当用户询问产品相关问题时，先使用 RAG 检索相关产品信息，然后结合信息回答用户
2. 当用户询问订单或物流信息时，使用相应的工具查询
3. 当用户需要退换货时，引导用户提供必要信息并帮助创建申请
4. 如果信息不明确，主动向用户询问

注意事项：
- 始终保持礼貌和专业
- 不要编造信息，如果不确定，告诉用户需要查询
- 对于复杂问题，分步骤解决
- 记住用户的上下文信息

当前可用的工具：
- search_products: 搜索产品
- get_product_details: 获取产品详情
- get_order_info: 获取订单信息
- get_user_orders: 获取用户订单列表
- get_tracking_status: 查询物流状态
- create_return_request: 创建退换货申请
- get_return_request_status: 查询退换货申请状态
- get_user_return_requests: 获取用户退换货申请列表

RAG 上下文信息：
{context}

请根据以上信息和工具，为用户提供最好的服务。"""


class ECommerceAgent:
    """电商智能客服代理"""
    
    def __init__(self):
        self.config = load_config()
        self.llm = self._init_llm()
        self.graph = self._build_graph()
    
    def _init_llm(self):
        """初始化大语言模型"""
        model_config = self.config.current_model_config
        return ChatOpenAI(
            api_key=model_config.api_key,
            model=model_config.model,
            base_url=model_config.base_url,
            temperature=model_config.temperature
        )
    
    def _build_graph(self):
        """构建 LangGraph 工作流"""
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 定义节点
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(tools))
        
        # 定义边
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        workflow.add_edge("tools", "agent")
        
        # 编译图
        return workflow.compile()
    
    def _retrieve_context(self, state: AgentState) -> AgentState:
        """检索 RAG 上下文"""
        messages = state["messages"]
        last_message = messages[-1] if messages else None
        
        if isinstance(last_message, HumanMessage):
            # 从用户消息中检索相关上下文
            context = product_rag.get_context(last_message.content, k=3)
        else:
            context = None
        
        return {"context": context}
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """代理节点：处理用户消息并决定是否调用工具"""
        messages = state["messages"]
        context = state.get("context")
        
        # 构建提示词
        system_prompt = SYSTEM_PROMPT.format(context=context or "暂无相关产品信息")
        
        # 绑定工具
        llm_with_tools = self.llm.bind_tools(tools)
        
        # 将系统提示词注入到消息列表
        full_messages: List[BaseMessage] = [SystemMessage(content=system_prompt)] + messages
        
        # 调用 LLM（带工具）
        response = llm_with_tools.invoke(full_messages)
        
        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """决定是否继续（是否需要调用工具）"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # 检查是否有工具调用
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        return "end"
    
    def chat(self, user_message: str, user_id: str = "USER001", history: Optional[List[BaseMessage]] = None) -> str:
        """
        与代理进行对话
        
        Args:
            user_message: 用户消息
            user_id: 用户ID
            history: 历史消息列表
            
        Returns:
            代理的回复
        """
        # 准备初始状态
        initial_state: AgentState = {
            "messages": history or [],
            "user_id": user_id,
            "context": None
        }
        
        # 添加用户消息
        initial_state["messages"].append(HumanMessage(content=user_message))
        
        # 执行图
        result = self.graph.invoke(initial_state)
        
        # 获取最后一条 AI 消息
        messages = result["messages"]
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                return message.content
        
        return "抱歉，我无法处理您的请求。"
    
    def stream_chat(self, user_message: str, user_id: str = "USER001", history: Optional[List[BaseMessage]] = None):
        """
        流式对话
        
        Args:
            user_message: 用户消息
            user_id: 用户ID
            history: 历史消息列表
            
        Yields:
            流式输出的内容
        """
        # 准备初始状态
        initial_state: AgentState = {
            "messages": history or [],
            "user_id": user_id,
            "context": None
        }
        
        # 添加用户消息
        initial_state["messages"].append(HumanMessage(content=user_message))
        
        # 流式执行图
        for output in self.graph.stream(initial_state):
            for node, value in output.items():
                if "messages" in value:
                    for msg in value["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            yield msg.content


# 全局代理实例
agent = ECommerceAgent()
