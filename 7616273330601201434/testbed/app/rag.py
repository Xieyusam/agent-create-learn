from typing import List, Dict, Any
FALLBACK = False
try:
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.retrievers import BM25Retriever
    try:
        from langchain.retrievers import EnsembleRetriever
    except Exception:
        from langchain.retrievers.ensemble import EnsembleRetriever  # type: ignore
except Exception:
    FALLBACK = True

PRODUCT_KNOWLEDGE_BASE = [
    {
        "content": """智能手表 Pro 产品说明：
- 产品名称：智能手表 Pro
- 产品型号：SW-PRO-2024
- 价格：1299元
- 主要功能：
  * 心率监测：24小时实时监测，精度±2bpm
  * GPS定位：支持GPS、GLONASS、北斗三星定位
  * 防水等级：50米防水，可游泳佩戴
  * 电池续航：日常使用14天，GPS模式36小时
  * 屏幕：1.43英寸AMOLED高清屏幕，分辨率466x466
  * 健康监测：血氧监测、压力监测、睡眠分析
- 保修政策：全国联保，质保1年
- 包装清单：手表×1、充电底座×1、说明书×1、保修卡×1""",
        "metadata": {"category": "智能穿戴", "product_id": "P001"}
    },
    {
        "content": """无线蓝牙耳机 产品说明：
- 产品名称：无线蓝牙耳机
- 产品型号：TWS-PRO-2024
- 价格：399元
- 主要功能：
  * 主动降噪：深度可达-42dB，支持通透模式
  * 续航时间：单次充电8小时，配合充电盒30小时
  * 蓝牙版本：5.3，支持AAC、LDAC编码
  * 音质：10mm动圈单元，Hi-Res认证
  * 通话：双麦克风AI降噪，通话清晰
  * 防水等级：IPX5，防汗防雨
- 保修政策：全国联保，质保1年
- 包装清单：耳机×2、充电盒×1、Type-C充电线×1、说明书×1、保修卡×1、备用耳塞×3对""",
        "metadata": {"category": "音频设备", "product_id": "P002"}
    },
    {
        "content": """便携充电宝 20000mAh 产品说明：
- 产品名称：便携充电宝 20000mAh
- 产品型号：PB-20K-2024
- 价格：199元
- 主要功能：
  * 容量：20000mAh（74Wh），可带上飞机
  * 输入：USB-C PD 65W快充
  * 输出：USB-C PD 65W、USB-A 22.5W、无线充电15W
  * 端口：2×USB-A、1×USB-C、1×无线充电
  * 显示：LED电量显示，精确到1%
  * 安全保护：过充保护、过放保护、短路保护、温度保护
- 保修政策：全国联保，质保1年
- 包装清单：充电宝×1、Type-C充电线×1、说明书×1、保修卡×1""",
        "metadata": {"category": "移动电源", "product_id": "P003"}
    },
    {
        "content": """机械键盘 RGB 产品说明：
- 产品名称：机械键盘 RGB
- 产品型号：KB-MX-RGB-2024
- 价格：599元
- 主要功能：
  * 轴体：Cherry MX轴体（红轴/青轴/茶轴可选）
  * 按键：104键全尺寸，全键无冲
  * 背光：1680万色RGB背光，支持多种灯效
  * 连接：有线USB-C，键线分离
  * 材质：铝合金上盖，PBT键帽
  * 人体工学：6°倾角设计，附赠腕托
- 保修政策：全国联保，质保2年
- 包装清单：键盘×1、Type-C数据线×1、腕托×1、拔键器×1、说明书×1、保修卡×1""",
        "metadata": {"category": "电脑配件", "product_id": "P004"}
    },
    {
        "content": """4K高清摄像头 产品说明：
- 产品名称：4K高清摄像头
- 产品型号：CAM-4K-2024
- 价格：499元
- 主要功能：
  * 分辨率：4K UHD (3840×2160) @30fps，1080P @60fps
  * 对焦：自动对焦，对焦距离10cm-无限远
  * 麦克风：双麦克风阵列，AI降噪
  * 视角：90°广角，支持数字变焦
  * 连接：USB 2.0，即插即用
  * 兼容：Windows、macOS、Linux、Chrome OS
- 保修政策：全国联保，质保1年
- 包装清单：摄像头×1、USB数据线×1、说明书×1、保修卡×1""",
        "metadata": {"category": "电脑配件", "product_id": "P005"}
    },
    {
        "content": """退换货政策：
1. 退货政策：
   - 自签收之日起7天内，商品完好可无理由退货
   - 商品需保持原包装、配件齐全、无人为损坏
   - 退款将在收到退货并确认无误后1-3个工作日内原路返回
   
2. 换货政策：
   - 自签收之日起15天内，商品存在质量问题可申请换货
   - 换货需保持商品完好、包装齐全
   - 换货产生的运费由商家承担
   
3. 不适用退换货的情况：
   - 商品已损坏或有人为使用痕迹
   - 包装、配件、发票等不齐全
   - 定制商品、虚拟商品
   - 超过退换货期限
   
4. 退换货流程：
   1. 在订单详情页提交退换货申请
   2. 等待客服审核（1-3个工作日）
   3. 审核通过后，按照提供的地址寄回商品
   4. 商家收到商品并确认无误后，处理退款或换货""",
        "metadata": {"category": "政策", "type": "return_policy"}
    },
    {
        "content": """物流配送说明：
1. 配送范围：
   - 中国大陆地区（港澳台及海外暂不支持）
   - 偏远地区（新疆、西藏、青海、宁夏、内蒙古）配送时间可能延长
   
2. 配送时效：
   - 普通快递：下单后24小时内发货，3-5个工作日送达
   - 顺丰速运：下单后24小时内发货，1-3个工作日送达
   - 偏远地区：5-7个工作日送达
   
3. 配送费用：
   - 订单满99元免运费
   - 订单不满99元，运费10元
   - 顺丰速运需额外支付15元运费
   
4. 签收注意事项：
   - 请在签收前检查商品包装是否完好
   - 如发现包装损坏或商品缺失，请拒收并联系客服
   - 签收后如发现商品质量问题，请在7天内申请退换货""",
        "metadata": {"category": "政策", "type": "shipping_policy"}
    },
    {
        "content": """支付方式说明：
1. 支持的支付方式：
   - 支付宝
   - 微信支付
   - 银联支付
   - 银行卡支付（支持储蓄卡和信用卡）
   
2. 支付安全：
   - 所有支付均通过加密通道传输
   - 不存储用户的支付密码和银行卡信息
   - 支持指纹支付和面容支付
   
3. 发票说明：
   - 支持开具电子发票和纸质发票
   - 电子发票将在订单完成后发送到您的邮箱
   - 纸质发票将随商品一起寄出（需额外支付5元运费）
   - 发票抬头可填写个人或公司名称""",
        "metadata": {"category": "政策", "type": "payment_policy"}
    }
]

if not FALLBACK:
    class ProductRAG:
        def __init__(self, vector_store_path: str = "./vector_store"):
            self.vector_store_path = vector_store_path
            self.embeddings = HuggingFaceEmbeddings(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.vector_store = None
            self.ensemble_retriever = None
            self._initialize_retrievers()
        
        def _initialize_retrievers(self):
            documents = []
            for item in PRODUCT_KNOWLEDGE_BASE:
                doc = Document(
                    page_content=item["content"],
                    metadata=item["metadata"]
                )
                documents.append(doc)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
            )
            split_docs = text_splitter.split_documents(documents)
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            faiss_retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            bm25_retriever = BM25Retriever.from_documents(split_docs)
            bm25_retriever.k = 3
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, faiss_retriever],
                weights=[0.5, 0.5]
            )
        
        def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
            if not self.ensemble_retriever:
                return []
            docs = self.ensemble_retriever.invoke(query)
            results = []
            for doc in docs[:k]:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 0.0
                })
            return results
        
        def get_context(self, query: str, k: int = 3) -> str:
            results = self.search(query, k=k)
            if not results:
                return ""
            context_parts = []
            for i, result in enumerate(results, 1):
                context_parts.append(f"[相关信息 {i}]\n{result['content']}")
            return "\n\n".join(context_parts)
else:
    class ProductRAG:
        def __init__(self, vector_store_path: str = "./vector_store"):
            self.vector_store_path = vector_store_path
            self.embeddings = object()
            self.vector_store = {}
        def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
            q = (query or "").strip()
            results = []
            for item in PRODUCT_KNOWLEDGE_BASE:
                text = item["content"]
                if q and (q in text):
                    results.append({"content": text, "metadata": item["metadata"], "score": 0.0})
            if not results:
                for item in PRODUCT_KNOWLEDGE_BASE:
                    if q in item["metadata"].get("category",""):
                        results.append({"content": item["content"], "metadata": item["metadata"], "score": 0.0})
            if not results:
                for item in PRODUCT_KNOWLEDGE_BASE[:max(1, k or 1)]:
                    results.append({"content": item["content"], "metadata": item["metadata"], "score": 0.0})
            return results[:k] if k else results
        def get_context(self, query: str, k: int = 3) -> str:
            rs = self.search(query, k=k)
            if not rs:
                return ""
            parts = []
            for i, r in enumerate(rs, 1):
                parts.append(f"[相关信息 {i}]\n{r['content']}")
            return "\n\n".join(parts)
