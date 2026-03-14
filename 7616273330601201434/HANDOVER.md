# 智能电商客服系统（testbed）交接文档

本文面向接手本仓库的工程师，聚焦“能做什么”和“关键实现怎么做”。阅读本篇可快速理解系统功能、核心流程与关键代码，便于继续开发与运维。

## 一、项目概览

- 场景：电商客服助手，支持产品问答、订单物流、退换货、用户偏好记录等。
- 能力：对话、工具调用、RAG 检索增强、用户长期记忆、基于 LangGraph 的工作流。
- 入口：`main.py`，交互式 CLI。
- 目录：业务代码位于 `app/`，配置在 `config.yaml`，依赖见 `requirements.txt`，单测在 `tests/`。

## 二、运行与测试

- 环境
  - Python 3.11+（推荐虚拟环境）
  - 配置 `.env`：参考 [`.env.example`](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/.env.example)
    - 必填：`DOUBAO_API_KEY`
  - 配置 [`config.yaml`](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/config.yaml)（支持从 `.env` 引用）
- 安装与启动
  - `pip install -r testbed/requirements.txt`
  - 切换到 `testbed` 目录后运行：`python main.py`
- 运行测试
  - 在 `testbed` 目录：`pytest tests/ -v`

## 三、整体架构与数据流

- 交互入口：[main.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/main.py#L36-L93)
  - 读取配置 → 初始化 `CustomerServiceAgent` → 进入输入循环 → 将用户输入与历史交给 Agent → 输出回复。
- Agent 编排：[customer_service.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L31-L57)
  - 加载配置与 LLM → 初始化 RAG 与工具 → 构建 LangGraph 工作流 → 提供 `chat/stream_chat`。
- 工具层：[tools.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py)
  - 产品/订单/退换货/用户偏好工具，供 LLM 以“函数调用”方式使用。
- RAG 层：[rag.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/rag.py)
  - 基于产品知识库，提供 `search` 与 `get_context`。支持带 FAISS 的完整实现与无依赖的回退实现。
- 记忆层：[memory.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/memory.py)
  - 使用 ChromaDB（或内存回退）维护用户画像文本，供回答时个性化增强。

## 四、关键流程拆解

### 1. 对话与工作流

- 初始化与系统提示词  
  - 构造见：[CustomerServiceAgent.__init__](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L31-L57)  
  - 系统提示词见：[_get_system_prompt](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L98-L121)
- 工作流编排（LangGraph）  
  - 构建见：[_build_graph](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L156-L175)  
  - 判断是否需要工具：[_should_continue](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L123-L129)（若 LLM 输出包含 `tool_calls` → 进入工具节点）
- 调用 LLM 与拼装上下文  
  - 关键逻辑：[_call_model](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L130-L154)  
  - 将系统提示词、RAG 上下文与对话历史发送给 `llm_with_tools.invoke`
- 对外接口  
  - 单次对话：[chat](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L183-L201)  
  - 流式对话：[stream_chat](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L203-L219)

### 2. 工具调用（Tools）

工具均在 [`tools.py`](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py) 定义，并通过 `@tool` 暴露：

- 产品相关
  - [search_product](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L173-L183)：关键词搜索 `PRODUCTS_DB`
  - [get_product_details](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L185-L191)：按 ID 返回详情
  - [get_all_products](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L212-L215)：返回全量产品
- 订单/物流
  - [query_order_status](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L192-L195)：查询订单状态与轨迹
  - [get_all_orders](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L207-L210)：按用户返回订单
- 退换货
  - [create_return_request](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L197-L201)：创建退/换货申请
  - [query_return_status](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L202-L205)：查询申请状态
- 用户偏好
  - [update_user_preference](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L217-L223)：写入用户画像文本（见 Memory）

内部模拟系统：

- 订单系统：[`OrderTrackingSystem`](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L61-L101) 提供 `orders_db/returns_db`，含物流轨迹生成逻辑。

### 3. RAG 检索增强（ProductRAG）

- 知识库：`PRODUCT_KNOWLEDGE_BASE`（产品说明、政策等）  
- 完整实现（安装依赖可用）：  
  - 初始化与切分、索引：[rag.py:L166-L199](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/rag.py#L166-L199)  
  - 检索与拼上下文：[rag.py:L200-L221](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/rag.py#L200-L221)
- 无依赖回退（默认可用）：  
  - 朴素匹配与上下文拼接：[rag.py:L222-L249](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/rag.py#L222-L249)
- 在 Agent 中的使用：在 [_call_model](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L140-L153) 中根据最后一条用户消息进行 `rag.get_context`，将相关片段附加到系统消息。

### 4. 用户长期记忆（Memory）

- 存储实现：[memory.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/memory.py)  
  - 优先使用 ChromaDB（`CHROMA_DB_PATH` 可配置）；缺少依赖则自动回退到进程内存字典。
  - 读取：[get_user_profile](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/memory.py#L27-L37)；写入：[update_user_profile](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/memory.py#L39-L52)。
- 与工具的衔接：通过 [update_user_preference](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L217-L223) 写入用户偏好；在 Agent 拼接系统提示词时附加用户画像（更个性化的回答）。

## 五、配置要点

- 模型配置：[`config.yaml`](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/config.yaml)
  - 通过 `current_model` 选择模型，实际参数从 `models[current_model]` 读取。
  - `api_key` 支持 `${ENV_NAME}` 占位符，具体由 [_load_config](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L58-L63) 展开。
- 配置校验：[_validate_config](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L64-L82)
  - 要求：存在有效 `current_model`；`api_key/model/base_url` 非空且不是占位符；否则抛出错误。
- LLM 初始化：[_init_llm](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L83-L96)
  - 优先使用 `langchain_openai.ChatOpenAI`，失败则使用占位类，便于在无依赖/离线环境跑通单测。

## 六、关键代码解读

- 容错与回退
  - LLM、RAG、Tool 装饰器均做了“无第三方依赖也可跑”的降级处理，利于本地开发与单测稳定性。
  - 例如 `tools.tool` 自定义装饰器在 `langchain_core` 缺失时兜底，[tools.py:L2-L13](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L2-L13)。
- 工作流编排最小循环
  - Agent → 判断是否需要工具 → Tools → Agent，直到模型不再返回 `tool_calls`，[customer_service._build_graph](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L156-L175)。
- 上下文拼接策略
  - 若命中 RAG，则将“系统提示词+相关片段”作为系统消息放在消息最前，有助于引导模型引用事实，[customer_service._call_model](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/customer_service.py#L146-L154)。
- 物流轨迹生成
  - 基于发货时间按 6 小时步进生成多段轨迹，便于展示“在途→派送中”的链路，[tools.OrderTrackingSystem._generate_tracking_history](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/app/tools.py#L109-L128)。

## 七、测试覆盖

- 单测位置：[`tests/`](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/tests)
  - 工具用例与集成流转：[test_customer_service.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/tests/test_customer_service.py)
  - 配置与工作流初始化：[test_config_chain.py](file:///k:/lang-project/agent-ai-project/7616273330601201434/testbed/tests/test_config_chain.py)
- 说明
  - 测试用例大量使用 `mock/patch` 脱离外部依赖，聚焦业务逻辑正确性。
  - 跑测命令：`pytest tests/ -v`

## 八、二次开发建议

- 工具层扩展
  - 将 `PRODUCTS_DB/OrderTrackingSystem` 替换为真实服务接口（建议封装适配层，保持工具签名稳定）。
- RAG 知识库
  - 将产品数据与政策文档接入向量库，定期增量构建；合理选择中文向量模型与分词器。
- 多用户与多会话
  - 将 `user_id` 贯穿调用链并接入持久化消息/画像存储；配合会话隔离策略。
- 评测与观测
  - 接入调用日志与提示词版本管理，建立“工具调用正确率/答案引用率/用户满意度”等指标。

---

如需深入某段实现，可直接点击上文的“代码引用”链接定位到对应文件与行号。

