from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Product(BaseModel):
    """产品模型"""
    id: str
    name: str
    description: str
    price: float
    category: str
    stock: int
    features: List[str] = Field(default_factory=list)


class OrderItem(BaseModel):
    """订单项模型"""
    product_id: str
    product_name: str
    quantity: int
    price: float


class Order(BaseModel):
    """订单模型"""
    id: str
    user_id: str
    items: List[OrderItem]
    total_amount: float
    status: str  # pending, paid, shipped, delivered, cancelled
    created_at: datetime
    shipping_address: str
    tracking_number: Optional[str] = None


class ReturnRequest(BaseModel):
    """退换货申请模型"""
    id: str
    order_id: str
    user_id: str
    reason: str
    type: str  # return, exchange
    status: str  # pending, approved, rejected, completed
    created_at: datetime
    description: Optional[str] = None