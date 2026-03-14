# 智能电商客服系统

基于 LangChain 和 LangGraph 实现的智能电商客服助手，支持自然语言对话、产品查询、订单物流查询和退换货处理。

## 功能特性

1. **Conversation 能力** - 支持自然语言对话
2. **Memory 能力** - 支持多轮对话历史记忆
3. **Tools 能力** - 集成多种工具（产品查询、订单查询、退换货处理）
4. **Workflow 能力** - 基于 LangGraph 的工作流编排
5. **RAG 能力** - 基于产品知识库的检索增强生成

## 技术栈

- **LangChain** >= 1.0.0
- **LangGraph** >= 1.0.0
- **Python** >= 3.11
- **FAISS** - 向量数据库
- **Sentence-Transformers** - 文本嵌入模型

## 项目结构

```
.
├── main.py                 # 项目启动文件
├── .env.example            # 环境变量示例
├── config.yaml             # 大模型配置文件
├── requirements.txt        # 项目依赖
├── app/                    # 业务代码目录
│   ├── tools.py            # 工具函数（产品、订单、退换货）
│   ├── rag.py              # RAG 系统（产品知识库）
│   ├── memory.py           # 用户长期记忆管理
│   └── customer_service.py # 客服代理核心逻辑
├── tests/                  # 测试目录
│   ├── test_customer_service.py # 业务与工作流测试
│   └── test_config_chain.py     # 配置链路测试
└── README.md               # 项目说明文档
```

## 安装与启动

1. 克隆或下载项目到本地

2. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 API Key
   ```

3. 手动启动：
   ```bash
   # 创建并激活虚拟环境（推荐 .venv）
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate

   # 安装依赖
   pip install -r requirements.txt

   # 启动
   python main.py
   ```

## 配置说明

项目使用 `.env` 文件管理敏感信息，`config.yaml` 管理一般配置。

1. **环境变量 (.env)**
   ```ini
   DOUBAO_API_KEY=your_api_key_here
   CHROMA_DB_PATH=./chroma_db
   ```

2. **配置文件 (config.yaml)**
   ```yaml
   current_model: "doubao-seed-2.0"
   models:
     doubao-seed-2.0:
       api_key: "${DOUBAO_API_KEY}"  # 引用环境变量
       ...
   ```

### 示例对话

**产品查询：**
```
👤 用户: 你们有什么智能手表？
🤖 客服: 我们有一款"智能手表 Pro"，价格是1299元。它支持心率监测、GPS定位、50米防水等功能，日常使用续航可达14天。需要我为您提供更详细的信息吗？
```

**订单查询：**
```
👤 用户: 帮我查一下 ORD001 订单的物流状态
🤖 客服: 好的，我来帮您查询 ORD001 订单的物流状态。

订单信息：
- 订单号：ORD001
- 商品：智能手表 Pro
- 当前状态：已发货
- 物流公司：顺丰速运
- 运单号：SF1234567890
- 预计送达：2024-01-18

物流轨迹：
1. 2024-01-16 09:00:00 - 已揽收
2. 2024-01-16 15:00:00 - 到达【北京转运中心】
3. 2024-01-16 21:00:00 - 到达【上海转运中心】
4. 2024-01-17 03:00:00 - 到达【广州分拨中心】
5. 2024-01-17 09:00:00 - 正在派送中

您的订单正在派送中，预计今天就能送达！
```

**退换货申请：**
```
👤 用户: 我想申请 ORD002 的退货
🤖 客服: 好的，我来帮您处理退货申请。请问退货的原因是什么呢？比如：质量问题、尺寸不合适、不想要了等。

👤 用户: 不想要了
🤖 客服: 好的，我来为您创建退货申请。

退换货申请已提交成功！
- 申请编号：RET001
- 订单号：ORD002
- 商品：无线蓝牙耳机
- 退货原因：不想要了
- 当前状态：待审核
- 预计处理时间：1-3个工作日

下一步：请等待客服审核，审核通过后会发送退货地址到您的邮箱。

还有什么我可以帮您的吗？
```

## 运行测试

项目包含完整的单元测试，覆盖配置链路、RAG、工具、工作流等核心功能（当前共 25 个用例）：

```bash
pytest tests/ -v
```

或者使用以下命令运行测试并查看覆盖率：

```bash
pytest tests/ -v --cov=. --cov-report=html
```

注意：
- 需要 Python >= 3.11；
- 首次运行请先创建 .venv 并安装依赖；
- .env 中的 DOUBAO_API_KEY 必须配置有效值。

## 工具说明

### 产品查询工具
- `search_product(query)` - 根据关键词搜索产品
- `get_product_details(product_id)` - 获取产品详细信息
- `get_all_products()` - 获取所有产品列表

### 订单查询工具
- `query_order_status(order_id)` - 查询订单状态和物流信息
- `get_all_orders(user_id)` - 获取用户的所有订单

### 退换货工具
- `create_return_request(order_id, reason, return_type, description)` - 创建退换货申请
- `query_return_status(return_id)` - 查询退换货申请状态

## 数据说明

项目使用模拟数据，包含：
- 5个产品（智能手表、耳机、充电宝、键盘、摄像头）
- 3个订单（不同状态）
- 完整的产品知识库

您可以根据实际需求修改 `tools.py` 中的数据库和 `rag.py` 中的知识库。

## 配置说明

### 支持的模型

您可以在 `config.yaml` 中配置多个模型，然后通过 `current_model` 切换：

```yaml
current_model: "doubao-seed-2.0"

models:
  doubao-seed-2.0:
    api_key: "your-api-key"
    model: "doubao-seed-2-0-code-preview-260215"
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
    temperature: 0.1
  
  gpt-4:
    api_key: "your-openai-key"
    model: "gpt-4"
    base_url: "https://api.openai.com/v1"
    temperature: 0.1
```

### 温度参数

- `temperature: 0.1` - 适合客服场景，输出更稳定、更准确
- 可以根据需要调整，范围 0-2
