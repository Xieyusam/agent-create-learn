# 智能电商客服工程复核报告

本报告依据 tips.md 与 must.md 的硬性要求，对 testbed 工程进行逐项核查与改进建议输出。结论优先体现阻塞问题，其次是推荐优化项，并附关键代码位置引用以便快速定位。

## 执行摘要（结论优先）

- 阻塞项（必须修复才能满足交付标准）
  - 根目录缺少 main.py、config.yaml、requirements.txt、tests/ 与 README.md（现均在 testbed 目录内），不符合“启动文件与配置入口在根目录”的交付规范。
  - 缺少基于 .env 的密钥管理与占位符解析能力；config.py 未加载 .env，也不支持 `${ENV_NAME}` 占位符替换，且未在缺失变量时抛出清晰错误。
  - 缺少 .env.example，且 .gitignore 未忽略 .env。
  - Memory 能力未按 must.md 要求使用 ChromaDB 存储用户画像，仅有内存中的对话历史管理，无长期记忆实现。
  - RAG 未采用 LangChain EnsembleRetriever 的混合检索，仅使用 FAISS；不符合 must.md 对“EnsembleRetriever（混合检索）+ Faiss”的要求。
  - 测试覆盖缺口：未覆盖配置链路（.env 占位符解析成功与缺失变量报错）、Workflow 主流程可初始化、RAG 本地文件存储与检索流程，以及 tips.md 中点名的自定义工具用例（见下文“测试覆盖差距”）。

- 重要改进项（建议尽快修复）
  - agent 节点未正确注入系统提示词；_agent_node 中构建的 prompt_messages 未使用，SYSTEM_PROMPT 实际未加入消息列表，影响回复质量。[agent.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/agent.py#L120-L135)
  - 文档与实现不完全一致：README 要求在 config.yaml 填写真实密钥，违背 tips.md 的安全规范；同时文档描述的项目结构与实际目录层级不一致（根与 testbed）。[README.md](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/README.md#L24-L37)
  - RAG 当前为内存构建的 FAISS，未提供本地持久化路径与复用策略，无法进行“本地文件存储与检索流程”的验证。[rag.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/rag.py#L59-L61)

## 逐项核对与差距

- 技术与版本要求
  - Python 3.11+：README 声明满足；未提供运行脚本，但可视为符合。
  - LangChain 1.0.0+、LangGraph 1.0.0+：requirements.txt 满足。[requirements.txt](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/requirements.txt)

- 入口与配置
  - 启动文件应位于根目录 main.py：当前 main.py 在 testbed 目录，需移动或在根提供启动入口包装。[main.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/main.py)
  - 配置文件应位于根目录 config.yaml：未提供；config.py 默认读取相对路径 “config.yaml”，在 testbed 运行时也会找不到根配置。[config.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/config.py#L26-L35)
  - 要求 .env.example、.env 加入 .gitignore：缺失；testbed/.gitignore 未包含 .env。[.gitignore](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/.gitignore#L42-L44)
  - config.yaml 中密钥字段必须采用 ${ENV_NAME} 占位符：未实现占位符解析与 .env 加载。

- 核心能力要求（must.md）
  - Conversation：已基于 LangChain ChatOpenAI 实现，并通过 LangGraph 组织流程。[agent.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/agent.py)
  - Memory：要求“长期记忆：使用 ChromaDB 存储用户画像”，当前仅内存会话管理（非 ChromaDB），缺失实现。[main.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/main.py#L14-L36)
  - Tools：已通过 @tool 定义多种电商工具，覆盖产品、订单、物流、退换货。[tools.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/tools.py)
  - Workflow：已基于 LangGraph StateGraph 实现，具备条件分支与工具节点。[agent.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/agent.py#L76-L101)
  - RAG：must.md 要求“EnsembleRetriever（混合检索）+ Faiss”。当前仅 FAISS + HuggingFaceEmbeddings，无 EnsembleRetriever。[rag.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/rag.py)
  - 自定义工具：must.md 点名 OrderTrackingSystem、ProductKnowledgeBase；现实现以函数工具存在，命名与职责未与 must.md 显式对齐（建议新增或封装具名工具）。

- 安全与文档一致性
  - 文档中存在直接在 config.yaml 写入真实 API Key 的示例，违反 tips.md 安全规范；需改为 ENV 占位符示例并在 README 明确配置流程。[README.md](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/README.md#L48-L59)
  - tips.md 要求“运行说明给出最短可执行路径”，当前根无启动文件，路径与文档不一致。

## 代码层面具体问题

- SYSTEM_PROMPT 未生效
  - _agent_node 中声明了 system_prompt 和 prompt_messages，但实际直接对 llm_with_tools.invoke(messages) 使用外部传入的 messages，未包含系统信息，提示词未注入；prompt_messages 变量未使用，属于死代码。[agent.py:L120-L135](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/agent.py#L120-L135)
  - 影响：模型缺少角色与流程约束，回答稳定性和工具调用意图识别会变差。

- RAG 缺少持久化与混合检索
  - 仅在内存中构建 FAISS；无索引落盘与复用路径；EnsembleRetriever 未集成。[rag.py:L59-L61](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/rag.py#L59-L61)

- 配置链路不支持 .env 与占位符
  - config.py 仅做 YAML 反序列化；未引入 dotenv 与占位符替换逻辑；缺少缺参报错与敏感信息保护策略。[config.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/config.py)

## 测试覆盖差距

- 必补测试（tips.md）
  - .env 占位符解析成功（示例：config.yaml 中 api_key: ${DOUBAO_API_KEY}，.env 中提供变量）。
  - 缺失环境变量时报错（清晰报错信息，指明缺失的 ENV 名）。
  - Workflow 主流程可初始化（StateGraph 可 compile，节点与条件边正确）。
  - RAG 本地文件存储与检索流程（索引落盘与加载复用）。
  - 自定义工具用例：tips.md 提及 ItineraryPlanner 与 FlightBookingSystem，与 must.md 中的工具命名存在不一致。建议以 must.md 为准，新增具名工具（ProductKnowledgeBase 与 OrderTrackingSystem）并补测；如需兼容 tips.md 示例，可提供别名或额外工具。

- 现有测试已覆盖
  - DataStore 基础能力、Tools 各功能、RAG 初始化与搜索、数据模型校验等均已覆盖。[test_ecommerce_agent.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/test_ecommerce_agent.py)

## 运维与安全合规差距

- 缺少 .env.example 与 .env 忽略规则；需在根 .gitignore 或现有 .gitignore 中追加 .env。
- README 中应避免指导用户在 config.yaml 写入真实密钥，改为 ENV 占位符示例，并说明 .env 与环境变量两种注入方式。
- 敏感信息输出规范：异常与日志中避免输出完整密钥（无直接问题，但须在后续实现中注意）。

## 建议的最小改造方案（按优先级）

1) 目录与启动入口对齐（阻塞）
   - 在根目录新增或移动以下文件：
     - main.py（作为统一入口，调用现有 testbed/main.py 或直接迁移实现）
     - config.yaml（仅占位符示例，不含真实密钥）
     - requirements.txt（合并 testbed/requirements.txt 到根）
     - tests/（将 testbed/test_ecommerce_agent.py 移至根 tests/ 并保留相对导入可用性）
     - README.md（运行路径与配置方式对齐根目录）

2) 配置链路与密钥管理（阻塞）
   - 在根添加 .env.example；在 .gitignore 中忽略 .env。
   - 修改 config.py：支持加载 .env（python-dotenv）、解析 YAML 中的 ${ENV_NAME} 占位符；缺失时抛出友好错误（包含 ENV 名）；禁止打印完整密钥。

3) RAG 能力升级（阻塞）
   - 集成 EnsembleRetriever：组合（向量检索 FAISS）+（BM25 等稀疏检索），使用 LangChain 的 EnsembleRetriever。
   - 增加 FAISS 持久化路径（例如 ./faiss_index/）与加载复用逻辑；提供索引不存在时重建机制。

4) Memory 能力实现（阻塞）
   - 采用 ChromaDB 存储用户画像与长期偏好；在 agent 流程中按 user_id 注入与更新画像。

5) 工具与命名对齐（重要改进）
   - 新增具名工具：ProductKnowledgeBase（包装产品知识检索/RAG）与 OrderTrackingSystem（包装物流与订单跟踪）。保留现有函数工具，便于兼容。

6) 测试补齐与文档一致性（重要改进）
   - 新增配置链路测试、Workflow 初始化测试、RAG 持久化测试、具名工具测试；更新 README 的测试数量与命令。

## 参考代码位置（便于修改）

- agent 工作流与提示词注入：[agent.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/agent.py)
- 配置加载与模型参数：[config.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/config.py)
- RAG 构建与检索：[rag.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/rag.py)
- 工具集合：[tools.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/tools.py)
- 单元测试现状：[test_ecommerce_agent.py](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/test_ecommerce_agent.py)
- 现有文档（需对齐安全规范与根路径）：[README.md](file:///k:/lang-project/agent-ai-project/2-7616273326827507494/testbed/README.md)

## 后续实施建议（最短路径）

- 第一步：在根创建入口与配置骨架（main.py、config.yaml 占位符、requirements.txt、.env.example、tests/）。
- 第二步：完善 config.py 的 .env 加载与占位符解析；补充配置相关单测。
+- 第三步：将 RAG 升级为 EnsembleRetriever，并增加 FAISS 本地持久化；补充相关单测。
+- 第四步：接入 ChromaDB 作为长期记忆；在 agent 流程中读写用户画像；补充单测。
+- 第五步：新增具名工具并补测；对齐 README，给出最短可执行路径与测试数量更新。

如需，我可以按上述优先级直接提交相应代码改造与测试补齐方案。*** End Patch}***/
