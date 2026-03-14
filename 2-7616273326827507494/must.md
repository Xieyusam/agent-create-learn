
智能助手本身具备的能力特性可以使用以下技术进行实现：
(1). Conversation 能力实现：基于 LangChain 的 Agent 类库实现（适用于需要自主规划和多步操作的复杂对话）
(2). Memory 能力实现：长期记忆：使用 ChromaDB 存储用户画像
(3). Tools 能力实现：使用 @tool 装饰器定义自定义工具函数
(4). Workflow 能力实现：基于 LangGraph StateGraph 实现包含循环和条件分支的复杂流程
(5). RAG 能力实现：检索实现：使用 LangChain EnsembleRetriever (混合检索)；存储实现：Faiss
(6). 自定义一些工具供自己使用，包括：
a. OrderTrackingSystem
b. ProductKnowledgeBase
要包含完整的单元测试，测试所有的功能，且全部通过。
要求代码架构清晰，代码书写优雅，包含必要的注释，符合优秀的工程规范。

必须注意：
核心框架版本要求
langchain (1.0.0+)
langgraph (1.0.0+)



