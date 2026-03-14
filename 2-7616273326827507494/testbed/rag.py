import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
try:
    from langchain.retrievers import EnsembleRetriever  # type: ignore
except Exception:  # 兼容旧版本无 EnsembleRetriever 的情况
    EnsembleRetriever = None  # type: ignore
    class _SimpleEnsemble:
        def __init__(self, retrievers, weights=None):
            self.retrievers = retrievers
            self.weights = weights or [1.0 for _ in retrievers]
        def get_relevant_documents(self, query: str):
            scored = {}
            for r, w in zip(self.retrievers, self.weights):
                # 兼容不同接口风格
                if hasattr(r, "get_relevant_documents"):
                    docs = r.get_relevant_documents(query)
                else:
                    docs = r.invoke(query)
                for rank, d in enumerate(docs):
                    key = (d.page_content, tuple(sorted(d.metadata.items())))
                    score = (len(docs) - rank) * w
                    scored[key] = (d, scored.get(key, (None, 0))[1] + score)
            # 根据累计分排序
            return [d for d, _s in sorted((val for val in scored.values()), key=lambda x: x[1], reverse=True)]
from data_store import data_store


class ProductRAG:
    """产品信息检索增强生成系统"""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.vector_store = None
        self.ensemble_retriever = None
        self._index_dir = Path("faiss_index")
        self._init_vector_store()
        self._init_retrievers()
    
    def _build_documents(self) -> List[Document]:
        """从产品数据构建文档集合"""
        documents: List[Document] = []
        for product in data_store.get_all_products():
            doc1 = Document(
                page_content=f"产品名称：{product.name}\n产品描述：{product.description}\n价格：{product.price}元\n分类：{product.category}",
                metadata={
                    "product_id": product.id,
                    "type": "basic_info",
                    "name": product.name
                }
            )
            documents.append(doc1)
            
            if product.features:
                features_text = "\n".join([f"- {feature}" for feature in product.features])
                doc2 = Document(
                    page_content=f"{product.name} 的产品特性：\n{features_text}",
                    metadata={
                        "product_id": product.id,
                        "type": "features",
                        "name": product.name
                    }
                )
                documents.append(doc2)
            
            doc3 = Document(
                page_content=f"{product.name} 的库存情况：当前有 {product.stock} 件库存",
                metadata={
                    "product_id": product.id,
                    "type": "stock",
                    "name": product.name
                }
            )
            documents.append(doc3)
        return documents

    def _init_vector_store(self):
        """初始化或加载向量存储（持久化）"""
        try:
            if self._index_dir.exists():
                self.vector_store = FAISS.load_local(
                    str(self._index_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                return
        except Exception:
            # 加载失败则重建
            self.vector_store = None
        
        documents = self._build_documents()
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        try:
            self._index_dir.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(str(self._index_dir))
        except Exception:
            # 持久化失败不影响运行
            pass

    def _init_retrievers(self):
        """初始化混合检索（BM25 + 向量检索）"""
        documents = self._build_documents()
        bm25 = BM25Retriever.from_documents(documents)
        dense = self.vector_store.as_retriever(search_kwargs={"k": 5})
        # 权重可调整，默认等权；兼容旧版本
        if EnsembleRetriever is not None:
            self.ensemble_retriever = EnsembleRetriever(retrievers=[bm25, dense], weights=[0.5, 0.5])  # type: ignore
        else:
            self.ensemble_retriever = _SimpleEnsemble([bm25, dense], weights=[0.5, 0.5])
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关产品信息
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            相关文档列表
        """
        if not self.vector_store:
            return []
        
        # 使用混合检索优先召回
        if self.ensemble_retriever:
            docs = self.ensemble_retriever.get_relevant_documents(query)
            docs = docs[:k]
        else:
            docs = self.vector_store.similarity_search(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": 0.0  # FAISS similarity_search 不返回分数，使用 similarity_search_with_score
            }
            for doc in docs
        ]
    
    def search_with_score(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关产品信息并返回相似度分数
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            相关文档列表，包含相似度分数
        """
        if not self.vector_store:
            return []
        
        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            }
            for doc, score in docs_with_scores
        ]
    
    def get_context(self, query: str, k: int = 3) -> str:
        """
        获取用于 RAG 的上下文信息
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            格式化的上下文文本
        """
        results = self.search_with_score(query, k=k)
        
        if not results:
            return "暂无相关产品信息"
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"【相关信息 {i}】\n{result['content']}")
        
        return "\n\n".join(context_parts)


# 全局 RAG 实例
product_rag = ProductRAG()
