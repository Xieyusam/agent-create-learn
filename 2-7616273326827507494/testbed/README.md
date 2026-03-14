# 智能电商客服系统

基于 LangChain 和 LangGraph 实现的智能电商客服系统，支持产品咨询、订单查询、物流跟踪和退换货申请等功能。

## 功能特性

1. **Tools 能力** - 集成多种工具，实现产品查询、订单管理、物流跟踪等功能
2. **Memory 能力** - 支持对话历史管理，保持上下文连贯性
3. **RAG 能力** - 基于产品信息的检索增强生成，提供准确的产品咨询
4. **Conversation 能力** - 自然语言对话，友好的用户交互
5. **Workflow 能力** - 基于 LangGraph 的工作流编排，实现复杂的业务逻辑

## 技术栈

- Python 3.11+
- LangChain 1.0.0+
- LangGraph 1.0.0+
- LangChain-OpenAI
- FAISS (向量数据库)
- Sentence-Transformers (嵌入模型)

## 项目结构

```
.
├── main.py                 # 主程序入口
├── config.py              # 配置管理
├── config.yaml            # 配置文件
├── models.py              # 数据模型定义
├── data_store.py          # 数据存储和模拟数据
├── tools.py               # 工具函数定义
├── rag.py                 # RAG 系统实现
├── agent.py               # 智能代理实现
├── test_ecommerce_agent.py # 单元测试
├── requirements.txt       # 项目依赖
└── README.md             # 项目说明
```

## 安装步骤

1. 克隆或下载项目到本地

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置大模型 API：
编辑 `config.yaml` 文件，填入您的 API 密钥：
```yaml
current_model: "doubao-seed-2.0"

models:
  doubao-seed-2.0:
    api_key: "your-api-key-here"  # 替换为您的 API 密钥
    model: "doubao-seed-2-0-code-preview-260215"
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
    temperature: 0.1
```

## 使用方法

### 启动客服系统

```bash
python main.py
```

### 交互命令

- 输入自然语言问题与客服对话
- 输入 `quit` 或 `exit` 退出系统
- 输入 `clear` 清除对话历史

### 示例对话

**产品咨询：**
```
您: 你们有什么智能手表？
小智: 我们有一款"智能手表 Pro"，价格是1999元。它支持心率监测、GPS定位、睡眠分析等功能，还有50米防水和14天续航。目前库存有50件。

您: 这款手表多少钱？
小智: 智能手表 Pro 的价格是1999元。
```

**订单查询：**
```
您: 帮我查一下订单 ORD001
小智: 订单 ORD001 的信息如下：
- 状态：已送达
- 总金额：3197.0元
- 下单时间：2024-01-15 00:00:00
- 收货地址：北京市朝阳区xxx街道xxx号
- 物流单号：SF1234567890
包含商品：
- 智能手表 Pro x 1 (1999.0元)
- 无线蓝牙耳机 x 2 (599.0元)
```

**物流跟踪：**
```
您: 帮我查一下物流 SF1234567890
小智: 物流单号 SF1234567890 的状态是：已签收
物流更新记录：
- 2024-01-18 14:30:00 - 快递已签收，签收人：本人
- 2024-01-18 09:00:00 - 快递员正在派送中
- 2024-01-17 18:00:00 - 快递已到达北京市朝阳区营业部
- 2024-01-16 12:00:00 - 快递已从深圳发出
```

**退换货申请：**
```
您: 我想申请退货
小智: 好的，我可以帮您处理退换货申请。请告诉我：
1. 您的订单号是什么？
2. 退换货的原因是什么？
3. 您是想退货还是换货？

您: 订单号是 ORD002，原因是不想要了，退货
小智: 好的，我来帮您创建退货申请。
退换货申请已提交成功！
申请编号：RET002
状态：待处理
我们会尽快处理您的申请，请耐心等待。
```

## 运行测试

项目包含完整的单元测试，覆盖所有功能模块。

运行所有测试：
```bash
pytest test_ecommerce_agent.py -v
```

运行特定测试类：
```bash
pytest test_ecommerce_agent.py::TestDataStore -v
```

生成测试覆盖率报告：
```bash
pytest test_ecommerce_agent.py --cov=. --cov-report=html
```

## 模拟数据

系统预置了以下模拟数据：

### 产品 (5个)
- P001: 智能手表 Pro - ¥1999
- P002: 无线蓝牙耳机 - ¥599
- P003: 便携充电宝 20000mAh - ¥199
- P004: 机械键盘 RGB - ¥399
- P005: 智能台灯 - ¥299

### 订单 (3个)
- ORD001: USER001 的订单（已送达）
- ORD002: USER001 的订单（运输中）
- ORD003: USER002 的订单（已支付）

### 退换货申请 (1个)
- RET001: USER001 的退货申请（待处理）

## 配置说明

### 模型配置

在 `config.yaml` 中可以配置多个模型，并通过 `current_model` 切换使用的模型：

```yaml
current_model: "doubao-seed-2.0"

models:
  doubao-seed-2.0:
    api_key: "your-api-key"
    model: "doubao-seed-2-0-code-preview-260215"
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
    temperature: 0.1
  
  # 可以添加更多模型配置
  another-model:
    api_key: "another-api-key"
    model: "model-name"
    base_url: "api-base-url"
    temperature: 0.7
```

### 系统提示词

在 `agent.py` 中的 `SYSTEM_PROMPT` 可以自定义客服的性格、职责和工作流程。

## 扩展开发

### 添加新工具

在 `tools.py` 中添加新的工具函数，并使用 `@tool` 装饰器：

```python
@tool
def my_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """
    工具描述（会被 LLM 读取）
    
    Args:
        param1: 参数1描述
        param2: 参数2描述
        
    Returns:
        返回值描述
    """
    # 工具实现
    return {"result": "success"}
```

然后将工具添加到 `tools` 列表中。

### 添加新数据

在 `data_store.py` 的 `_init_mock_data` 方法中添加新的模拟数据。

### 自定义 RAG

在 `rag.py` 中可以自定义嵌入模型、向量存储和检索策略。

## 注意事项

1. 首次运行时，RAG 系统会下载嵌入模型，需要网络连接
2. 请确保 API 密钥的安全性，不要将 `config.yaml` 提交到版本控制
3. 模拟数据仅供测试使用，生产环境需要连接真实的数据库
4. 建议在生产环境中使用更强大的嵌入模型和向量数据库

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎反馈。