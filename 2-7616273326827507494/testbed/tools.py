from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from data_store import data_store
from models import Product, Order, ReturnRequest
from datetime import datetime
from rag import product_rag


@tool
def search_products(keyword: str) -> List[Dict[str, Any]]:
    """
    搜索产品信息。
    
    Args:
        keyword: 搜索关键词，可以是产品名称、描述、分类或特性
        
    Returns:
        匹配的产品列表，包含产品ID、名称、价格、描述等信息
    """
    products = data_store.search_products(keyword)
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "category": p.category,
            "description": p.description,
            "stock": p.stock,
            "features": p.features
        }
        for p in products
    ]


@tool
def product_knowledge_base(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    产品知识库检索（RAG 封装）。
    通过混合检索返回与查询最相关的产品信息片段。
    """
    return product_rag.search(query, k=k)


@tool
def get_product_details(product_id: str) -> Optional[Dict[str, Any]]:
    """
    获取产品详细信息。
    
    Args:
        product_id: 产品ID
        
    Returns:
        产品详细信息，如果产品不存在则返回None
    """
    product = data_store.get_product(product_id)
    if not product:
        return None
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "description": product.description,
        "stock": product.stock,
        "features": product.features
    }


@tool
def get_order_info(order_id: str) -> Optional[Dict[str, Any]]:
    """
    获取订单信息。
    
    Args:
        order_id: 订单ID
        
    Returns:
        订单详细信息，如果订单不存在则返回None
    """
    order = data_store.get_order(order_id)
    if not order:
        return None
    return {
        "id": order.id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price": item.price
            }
            for item in order.items
        ]
    }


@tool
def get_user_orders(user_id: str) -> List[Dict[str, Any]]:
    """
    获取用户的所有订单。
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户的订单列表
    """
    orders = data_store.get_user_orders(user_id)
    return [
        {
            "id": order.id,
            "status": order.status,
            "total_amount": order.total_amount,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "tracking_number": order.tracking_number
        }
        for order in orders
    ]


@tool
def get_tracking_status(tracking_number: str) -> Dict[str, Any]:
    """
    获取物流状态信息。
    
    Args:
        tracking_number: 物流单号
        
    Returns:
        物流状态和更新记录
    """
    return data_store.get_tracking_info(tracking_number)


@tool
def order_tracking_system(tracking_number: str) -> Dict[str, Any]:
    """
    订单物流跟踪系统（封装）。
    提供物流状态与更新列表。
    """
    return data_store.get_tracking_info(tracking_number)

@tool
def create_return_request(
    order_id: str,
    user_id: str,
    reason: str,
    return_type: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建退换货申请。
    
    Args:
        order_id: 订单ID
        user_id: 用户ID
        reason: 退换货原因
        return_type: 申请类型，"return"（退货）或"exchange"（换货）
        description: 详细描述（可选）
        
    Returns:
        创建结果，包含申请ID和状态
    """
    # 验证订单是否存在
    order = data_store.get_order(order_id)
    if not order:
        return {"success": False, "message": f"订单 {order_id} 不存在"}
    
    # 验证订单是否属于该用户
    if order.user_id != user_id:
        return {"success": False, "message": "该订单不属于您"}
    
    # 生成申请ID
    return_id = f"RET{len(data_store.return_requests) + 1:03d}"
    
    # 创建申请
    return_request = ReturnRequest(
        id=return_id,
        order_id=order_id,
        user_id=user_id,
        reason=reason,
        type=return_type,
        status="pending",
        created_at=datetime.now(),
        description=description
    )
    
    data_store.create_return_request(return_request)
    
    return {
        "success": True,
        "message": "退换货申请已提交成功",
        "return_id": return_id,
        "status": "pending"
    }


@tool
def get_return_request_status(return_id: str) -> Optional[Dict[str, Any]]:
    """
    获取退换货申请状态。
    
    Args:
        return_id: 退换货申请ID
        
    Returns:
        申请详细信息，如果申请不存在则返回None
    """
    return_request = data_store.get_return_request(return_id)
    if not return_request:
        return None
    return {
        "id": return_request.id,
        "order_id": return_request.order_id,
        "reason": return_request.reason,
        "type": return_request.type,
        "status": return_request.status,
        "created_at": return_request.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "description": return_request.description
    }


@tool
def get_user_return_requests(user_id: str) -> List[Dict[str, Any]]:
    """
    获取用户的所有退换货申请。
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户的退换货申请列表
    """
    requests = data_store.get_user_return_requests(user_id)
    return [
        {
            "id": req.id,
            "order_id": req.order_id,
            "reason": req.reason,
            "type": req.type,
            "status": req.status,
            "created_at": req.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for req in requests
    ]


# 工具列表
tools = [
    search_products,
    get_product_details,
    get_order_info,
    get_user_orders,
    get_tracking_status,
    product_knowledge_base,
    order_tracking_system,
    create_return_request,
    get_return_request_status,
    get_user_return_requests
]
