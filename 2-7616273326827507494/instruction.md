帮我实现一个基于大模型的 智能电商客服，可以与我通过自然语言进行沟通，并通过调用大模型，以及自我实现的一些 Tools 完成以下任务：
回答用户关于产品的疑问
查询订单物流状态
处理退换货申请
该智能助手本身具备的能力特性包括：
Conversation 能力
Memory 能力
Tools 能力
Workflow 能力
RAG 能力
工程要求：
只能使用 LangChain 或者 LangGraph 实现，版本要求为 LangChain 1.0.0 以上，LangGraph 1.0.0 以上。
Python 版本要求为 3.11 及 以上。
项目的启动文件为根目录下的 main.py。
需要完成完整的单元测试，测试所有的功能，且全部通过。
关于大模型的配置信息，请写到项目根目录下的 config.yaml 文件中，具体格式如下：

# 当前使用的模型 (对应下方 models 中的 key)
current_model: "doubao-seed-2.0"

models:
  doubao-seed-2.0:
    api_key: "your-api-key"
    model: "doubao-seed-2-0-code-preview-260215"
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
    temperature: 0.1