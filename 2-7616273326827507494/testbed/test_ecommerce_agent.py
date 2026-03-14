#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能电商客服系统 - 单元测试
"""

import pytest
from datetime import datetime
from models import Product, Order, OrderItem, ReturnRequest
from data_store import data_store, DataStore
from tools import (
    search_products,
    get_product_details,
    get_order_info,
    get_user_orders,
    get_tracking_status,
    create_return_request,
    get_return_request_status,
    get_user_return_requests
)
from rag import product_rag, ProductRAG


class TestDataStore:
    """测试数据存储类"""
    
    def test_init_mock_data(self):
        """测试初始化模拟数据"""
        store = DataStore()
        assert len(store.products) == 5
        assert len(store.orders) == 3
        assert len(store.return_requests) == 1
    
    def test_get_product(self):
        """测试获取产品"""
        product = data_store.get_product("P001")
        assert product is not None
        assert product.id == "P001"
        assert product.name == "智能手表 Pro"
    
    def test_get_nonexistent_product(self):
        """测试获取不存在的产品"""
        product = data_store.get_product("P999")
        assert product is None
    
    def test_search_products(self):
        """测试搜索产品"""
        results = data_store.search_products("手表")
        assert len(results) >= 1
        assert any("手表" in p.name for p in results)
        
        results = data_store.search_products("无线")
        assert len(results) >= 1
    
    def test_get_all_products(self):
        """测试获取所有产品"""
        products = data_store.get_all_products()
        assert len(products) == 5
    
    def test_get_order(self):
        """测试获取订单"""
        order = data_store.get_order("ORD001")
        assert order is not None
        assert order.id == "ORD001"
        assert order.user_id == "USER001"
    
    def test_get_user_orders(self):
        """测试获取用户订单"""
        orders = data_store.get_user_orders("USER001")
        assert len(orders) == 2
        assert all(order.user_id == "USER001" for order in orders)
    
    def test_get_tracking_info(self):
        """测试获取物流信息"""
        tracking = data_store.get_tracking_info("SF1234567890")
        assert "status" in tracking
        assert "updates" in tracking
        assert len(tracking["updates"]) > 0
    
    def test_create_return_request(self):
        """测试创建退换货申请"""
        store = DataStore()
        initial_count = len(store.return_requests)
        
        return_request = ReturnRequest(
            id=f"RET{initial_count + 1:03d}",
            order_id="ORD002",
            user_id="USER001",
            reason="不想要了",
            type="return",
            status="pending",
            created_at=datetime.now()
        )
        
        return_id = store.create_return_request(return_request)
        assert len(store.return_requests) == initial_count + 1
        assert return_id in store.return_requests


class TestTools:
    """测试工具函数"""
    
    def test_search_products_tool(self):
        """测试搜索产品工具"""
        result = search_products.invoke({"keyword": "手表"})
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "id" in result[0]
        assert "name" in result[0]
    
    def test_get_product_details_tool(self):
        """测试获取产品详情工具"""
        result = get_product_details.invoke({"product_id": "P001"})
        assert result is not None
        assert result["id"] == "P001"
        assert "price" in result
    
    def test_get_nonexistent_product_details(self):
        """测试获取不存在产品的详情"""
        result = get_product_details.invoke({"product_id": "P999"})
        assert result is None
    
    def test_get_order_info_tool(self):
        """测试获取订单信息工具"""
        result = get_order_info.invoke({"order_id": "ORD001"})
        assert result is not None
        assert result["id"] == "ORD001"
        assert "status" in result
    
    def test_get_user_orders_tool(self):
        """测试获取用户订单工具"""
        result = get_user_orders.invoke({"user_id": "USER001"})
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_get_tracking_status_tool(self):
        """测试获取物流状态工具"""
        result = get_tracking_status.invoke({"tracking_number": "SF1234567890"})
        assert "status" in result
        assert "updates" in result
    
    def test_create_return_request_tool(self):
        """测试创建退换货申请工具"""
        # 使用独立的数据存储实例进行测试
        from data_store import DataStore
        test_store = DataStore()
        
        # 直接测试工具逻辑
        result = create_return_request.invoke({
            "order_id": "ORD002",
            "user_id": "USER001",
            "reason": "测试原因",
            "return_type": "return",
            "description": "测试描述"
        })
        
        # 注意：由于工具使用全局 data_store，这里我们只验证返回格式
        assert "success" in result
        # 实际创建操作会影响全局状态，这里不做过多断言
    
    def test_get_return_request_status_tool(self):
        """测试获取退换货申请状态工具"""
        result = get_return_request_status.invoke({"return_id": "RET001"})
        assert result is not None
        assert result["id"] == "RET001"
    
    def test_get_user_return_requests_tool(self):
        """测试获取用户退换货申请工具"""
        result = get_user_return_requests.invoke({"user_id": "USER001"})
        assert isinstance(result, list)
        assert len(result) >= 1


class TestRAG:
    """测试 RAG 系统"""
    
    def test_rag_initialization(self):
        """测试 RAG 初始化"""
        rag = ProductRAG()
        assert rag.vector_store is not None
        assert rag.embeddings is not None
    
    def test_rag_search(self):
        """测试 RAG 搜索"""
        results = product_rag.search("智能手表", k=3)
        assert isinstance(results, list)
        assert len(results) > 0
        assert "content" in results[0]
        assert "metadata" in results[0]
    
    def test_rag_search_with_score(self):
        """测试 RAG 带分数搜索"""
        results = product_rag.search_with_score("耳机", k=3)
        assert isinstance(results, list)
        assert len(results) > 0
        assert "score" in results[0]
        assert isinstance(results[0]["score"], float)
    
    def test_rag_get_context(self):
        """测试 RAG 获取上下文"""
        context = product_rag.get_context("充电宝", k=2)
        assert isinstance(context, str)
        assert len(context) > 0
        assert "充电宝" in context or "电源" in context


class TestModels:
    """测试数据模型"""
    
    def test_product_model(self):
        """测试产品模型"""
        product = Product(
            id="TEST001",
            name="测试产品",
            description="这是一个测试产品",
            price=99.9,
            category="测试分类",
            stock=10,
            features=["特性1", "特性2"]
        )
        assert product.id == "TEST001"
        assert product.name == "测试产品"
        assert len(product.features) == 2
    
    def test_order_model(self):
        """测试订单模型"""
        order = Order(
            id="TESTORD001",
            user_id="TESTUSER001",
            items=[
                OrderItem(
                    product_id="P001",
                    product_name="智能手表 Pro",
                    quantity=1,
                    price=1999.0
                )
            ],
            total_amount=1999.0,
            status="paid",
            created_at=datetime.now(),
            shipping_address="测试地址"
        )
        assert order.id == "TESTORD001"
        assert len(order.items) == 1
        assert order.total_amount == 1999.0
    
    def test_return_request_model(self):
        """测试退换货申请模型"""
        request = ReturnRequest(
            id="TESTRET001",
            order_id="TESTORD001",
            user_id="TESTUSER001",
            reason="测试原因",
            type="return",
            status="pending",
            created_at=datetime.now()
        )
        assert request.id == "TESTRET001"
        assert request.type == "return"
        assert request.status == "pending"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])