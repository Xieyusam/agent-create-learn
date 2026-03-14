import pytest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import langchain
    # print(f"LANGCHAIN FILE: {langchain.__file__}")
except Exception as e:
    print(f"Error importing langchain: {e}")

from unittest.mock import Mock, patch, MagicMock

from app.tools import (
    search_product,
    get_product_details,
    query_order_status,
    create_return_request,
    query_return_status,
    get_all_orders,
    get_all_products,
    PRODUCTS_DB,
    order_system
)
from app.rag import ProductRAG
from app.customer_service import CustomerServiceAgent, AgentState


class TestTools:
    """测试工具函数"""
    
    def test_search_product_found(self):
        """测试搜索产品 - 找到匹配"""
        results = search_product.invoke("智能手表")
        assert len(results) > 0
        assert any("智能手表" in p["name"] for p in results)
    
    def test_search_product_not_found(self):
        """测试搜索产品 - 未找到匹配"""
        results = search_product.invoke("不存在的产品")
        assert len(results) == 1
        assert "未找到" in results[0].get("message", "")
    
    def test_get_product_details_exists(self):
        """测试获取产品详情 - 产品存在"""
        product = get_product_details.invoke("P001")
        assert product["id"] == "P001"
        assert "name" in product
        assert "price" in product
    
    def test_get_product_details_not_exists(self):
        """测试获取产品详情 - 产品不存在"""
        product = get_product_details.invoke("P999")
        assert "error" in product
    
    def test_query_order_status_exists(self):
        """测试查询订单状态 - 订单存在"""
        order = query_order_status.invoke("ORD001")
        assert order["id"] == "ORD001"
        assert "status" in order
        assert "tracking_number" in order
    
    def test_query_order_status_not_exists(self):
        """测试查询订单状态 - 订单不存在"""
        order = query_order_status.invoke("ORD999")
        assert "error" in order
    
    def test_create_return_request_success(self):
        """测试创建退换货申请 - 成功"""
        # 清空之前的退换货记录
        order_system.returns_db.clear()
        
        result = create_return_request.invoke({
            "order_id": "ORD001",
            "reason": "质量问题",
            "return_type": "退货"
        })
        
        assert "return_id" in result
        assert result["status"] == "待审核"
        assert len(order_system.returns_db) == 1
    
    def test_create_return_request_order_not_exists(self):
        """测试创建退换货申请 - 订单不存在"""
        result = create_return_request.invoke({
            "order_id": "ORD999",
            "reason": "质量问题",
            "return_type": "退货"
        })
        
        assert "error" in result
    
    def test_query_return_status_exists(self):
        """测试查询退换货状态 - 申请存在"""
        # 先创建一个退换货申请
        order_system.returns_db.clear()
        create_return_request.invoke({
            "order_id": "ORD001",
            "reason": "质量问题",
            "return_type": "退货"
        })
        
        return_id = list(order_system.returns_db.keys())[0]
        result = query_return_status.invoke(return_id)
        
        assert result["id"] == return_id
        assert "status" in result
    
    def test_query_return_status_not_exists(self):
        """测试查询退换货状态 - 申请不存在"""
        result = query_return_status.invoke("RET999")
        assert "error" in result
    
    def test_get_all_orders(self):
        """测试获取所有订单"""
        orders = get_all_orders.invoke("U001")
        assert len(orders) > 0
        assert all(order["user_id"] == "U001" for order in orders)
    
    def test_get_all_products(self):
        """测试获取所有产品"""
        products = get_all_products.invoke({})
        assert len(products) == len(PRODUCTS_DB)


class TestRAG:
    """测试RAG系统"""
    
    def test_rag_initialization(self):
        """测试RAG初始化"""
        rag = ProductRAG()
        assert rag.vector_store is not None
        assert rag.embeddings is not None
    
    def test_rag_search(self):
        """测试RAG搜索"""
        rag = ProductRAG()
        results = rag.search("智能手表", k=2)
        assert len(results) > 0
        assert all("content" in r for r in results)
    
    def test_rag_get_context(self):
        """测试RAG获取上下文"""
        rag = ProductRAG()
        context = rag.get_context("无线耳机", k=2)
        assert isinstance(context, str)
        assert len(context) > 0


class TestCustomerServiceAgent:
    """测试客服代理"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {
            "current_model": "test-model",
            "models": {
                "test-model": {
                    "api_key": "test-key",
                    "model": "test-model-name",
                    "base_url": "https://test.api.com/v3",
                    "temperature": 0.1
                }
            }
        }
    
    @patch('app.customer_service.ChatOpenAI')
    @patch('app.customer_service.yaml.safe_load')
    def test_agent_initialization(self, mock_yaml_load, mock_chat_openai, mock_config):
        """测试代理初始化"""
        mock_yaml_load.return_value = mock_config
        mock_llm_instance = Mock()
        mock_chat_openai.return_value = mock_llm_instance
        
        agent = CustomerServiceAgent()
        
        assert agent.config == mock_config
        assert agent.llm is not None
        assert agent.tools is not None
        assert len(agent.tools) > 0
    
    @patch('app.customer_service.ChatOpenAI')
    @patch('app.customer_service.yaml.safe_load')
    def test_get_system_prompt(self, mock_yaml_load, mock_chat_openai, mock_config):
        """测试获取系统提示词"""
        mock_yaml_load.return_value = mock_config
        mock_llm_instance = Mock()
        mock_chat_openai.return_value = mock_llm_instance
        
        agent = CustomerServiceAgent()
        system_prompt = agent._get_system_prompt()
        
        assert isinstance(system_prompt, str)
        assert "电商客服" in system_prompt
        assert len(system_prompt) > 0
    
    @patch('app.customer_service.ChatOpenAI')
    @patch('app.customer_service.yaml.safe_load')
    def test_should_continue_with_tools(self, mock_yaml_load, mock_chat_openai, mock_config):
        """测试是否继续 - 需要调用工具"""
        mock_yaml_load.return_value = mock_config
        mock_llm_instance = Mock()
        mock_chat_openai.return_value = mock_llm_instance
        
        agent = CustomerServiceAgent()
        
        # 创建带有工具调用的消息
        mock_message = Mock()
        mock_message.tool_calls = [{"name": "test_tool"}]
        
        state = {
            "messages": [mock_message]
        }
        
        result = agent._should_continue(state)
        assert result == "tools"
    
    @patch('app.customer_service.ChatOpenAI')
    @patch('app.customer_service.yaml.safe_load')
    def test_should_continue_end(self, mock_yaml_load, mock_chat_openai, mock_config):
        """测试是否继续 - 结束"""
        mock_yaml_load.return_value = mock_config
        mock_llm_instance = Mock()
        mock_chat_openai.return_value = mock_llm_instance
        
        agent = CustomerServiceAgent()
        
        # 创建没有工具调用的消息
        mock_message = Mock()
        mock_message.tool_calls = []
        
        state = {
            "messages": [mock_message]
        }
        
        result = agent._should_continue(state)
        assert result == "__end__"


class TestIntegration:
    """集成测试"""
    
    def test_product_query_workflow(self):
        """测试产品查询工作流"""
        # 测试搜索产品
        search_results = search_product.invoke("耳机")
        assert len(search_results) > 0
        
        # 测试获取产品详情
        if search_results and "id" in search_results[0]:
            product_id = search_results[0]["id"]
            product_details = get_product_details.invoke(product_id)
            assert product_details["id"] == product_id
    
    def test_order_and_return_workflow(self):
        """测试订单和退换货工作流"""
        # 清空退换货记录
        order_system.returns_db.clear()
        
        # 测试查询订单
        order = query_order_status.invoke("ORD001")
        assert order["id"] == "ORD001"
        
        # 测试创建退换货申请
        return_result = create_return_request.invoke({
            "order_id": "ORD001",
            "reason": "不想要了",
            "return_type": "退货",
            "description": "试了一下不太喜欢"
        })
        
        assert "return_id" in return_result
        
        # 测试查询退换货状态
        return_status = query_return_status.invoke(return_result["return_id"])
        assert return_status["id"] == return_result["return_id"]
        assert return_status["status"] == "待审核"
    
    def test_rag_with_tools(self):
        """测试RAG与工具结合"""
        rag = ProductRAG()
        
        # 搜索产品信息
        search_results = search_product.invoke("充电宝")
        assert len(search_results) > 0
        
        # 使用RAG获取更多信息
        if search_results:
            product_name = search_results[0]["name"]
            rag_context = rag.get_context(product_name)
            assert len(rag_context) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
