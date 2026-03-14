from typing import Dict, Any, Optional, List
try:
    from langchain_core.tools import tool
except Exception:
    def tool(f):
        class _Tool:
            def invoke(self, *args, **kwargs):
                if args and isinstance(args[0], dict):
                    return f(**args[0])
                if args:
                    return f(*args)
                return f(**kwargs)
        return _Tool()
from datetime import datetime, timedelta
import random
from app.memory import memory_manager

PRODUCTS_DB = {
    "P001": {
        "id": "P001",
        "name": "智能手表 Pro",
        "price": 1299.0,
        "description": "高端智能手表，支持心率监测、GPS定位、50米防水",
        "stock": 50,
        "category": "智能穿戴"
    },
    "P002": {
        "id": "P002",
        "name": "无线蓝牙耳机",
        "price": 399.0,
        "description": "主动降噪，续航30小时，蓝牙5.3",
        "stock": 100,
        "category": "音频设备"
    },
    "P003": {
        "id": "P003",
        "name": "便携充电宝 20000mAh",
        "price": 199.0,
        "description": "大容量快充，支持多设备同时充电",
        "stock": 200,
        "category": "移动电源"
    },
    "P004": {
        "id": "P004",
        "name": "机械键盘 RGB",
        "price": 599.0,
        "description": "Cherry MX轴体，全键无冲，1680万色RGB背光",
        "stock": 30,
        "category": "电脑配件"
    },
    "P005": {
        "id": "P005",
        "name": "4K高清摄像头",
        "price": 499.0,
        "description": "4K分辨率，自动对焦，双麦克风降噪",
        "stock": 75,
        "category": "电脑配件"
    }
}

class OrderTrackingSystem:
    def __init__(self):
        self.orders_db = {
            "ORD001": {
                "id": "ORD001",
                "product_id": "P001",
                "product_name": "智能手表 Pro",
                "status": "已发货",
                "tracking_number": "SF1234567890",
                "logistics_provider": "顺丰速运",
                "create_time": "2024-01-15 10:30:00",
                "ship_time": "2024-01-16 09:00:00",
                "estimated_delivery": "2024-01-18",
                "user_id": "U001"
            },
            "ORD002": {
                "id": "ORD002",
                "product_id": "P002",
                "product_name": "无线蓝牙耳机",
                "status": "运输中",
                "tracking_number": "YT9876543210",
                "logistics_provider": "圆通速递",
                "create_time": "2024-01-17 14:20:00",
                "ship_time": "2024-01-18 08:00:00",
                "estimated_delivery": "2024-01-20",
                "user_id": "U001"
            },
            "ORD003": {
                "id": "ORD003",
                "product_id": "P003",
                "product_name": "便携充电宝 20000mAh",
                "status": "待发货",
                "tracking_number": None,
                "logistics_provider": None,
                "create_time": "2024-01-19 16:45:00",
                "ship_time": None,
                "estimated_delivery": "2024-01-22",
                "user_id": "U001"
            }
        }
        self.returns_db = {}

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders_db.get(order_id)

    def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        return [order for order in self.orders_db.values() if order["user_id"] == user_id]

    def _generate_tracking_history(self, order: Dict[str, Any]) -> List[Dict[str, str]]:
        history = []
        if not order.get("ship_time"):
            return history
        base_time = datetime.strptime(order["ship_time"], "%Y-%m-%d %H:%M:%S")
        locations = [
            "已揽收",
            "到达【北京转运中心】",
            "到达【上海转运中心】",
            "到达【广州分拨中心】",
            "正在派送中"
        ]
        for i, location in enumerate(locations):
            time = base_time + timedelta(hours=i * 6)
            history.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": location,
                "status": "运输中" if i < len(locations) - 1 else "派送中"
            })
        return history

    def query_order_status(self, order_id: str) -> Dict[str, Any]:
        if order_id in self.orders_db:
            order = self.orders_db[order_id].copy()
            if order["status"] in ["已发货", "运输中"]:
                order["tracking_history"] = self._generate_tracking_history(order)
            return order
        return {"error": f"订单ID {order_id} 不存在"}

    def create_return_request(self, order_id: str, reason: str, return_type: str = "退货", description: Optional[str] = None) -> Dict[str, Any]:
        if order_id not in self.orders_db:
            return {"error": f"订单ID {order_id} 不存在"}
        order = self.orders_db[order_id]
        if order["status"] not in ["已发货", "运输中", "已签收"]:
            return {"error": "当前订单状态不支持退换货申请"}
        return_id = f"RET{len(self.returns_db) + 1:03d}"
        return_request = {
            "id": return_id,
            "order_id": order_id,
            "product_id": order["product_id"],
            "product_name": order["product_name"],
            "reason": reason,
            "return_type": return_type,
            "description": description,
            "status": "待审核",
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": order["user_id"]
        }
        self.returns_db[return_id] = return_request
        return {
            "message": "退换货申请已提交成功",
            "return_id": return_id,
            "status": "待审核",
            "estimated_processing_time": "1-3个工作日",
            "next_steps": "请等待客服审核，审核通过后会发送退货地址到您的邮箱"
        }

    def query_return_status(self, return_id: str) -> Dict[str, Any]:
        if return_id in self.returns_db:
            return self.returns_db[return_id]
        return {"error": f"退换货申请ID {return_id} 不存在"}

order_system = OrderTrackingSystem()

@tool
def search_product(query: str) -> List[Dict[str, Any]]:
    """根据关键词在产品库中搜索匹配的产品列表。"""
    results = []
    query_lower = query.lower()
    for product in PRODUCTS_DB.values():
        if (query_lower in product["name"].lower() or 
            query_lower in product["description"].lower() or 
            query_lower in product["category"].lower()):
            results.append(product)
    return results if results else [{"message": "未找到匹配的产品"}]

@tool
def get_product_details(product_id: str) -> Dict[str, Any]:
    """根据产品ID返回产品详细信息。"""
    if product_id in PRODUCTS_DB:
        return PRODUCTS_DB[product_id]
    return {"error": f"产品ID {product_id} 不存在"}

@tool
def query_order_status(order_id: str) -> Dict[str, Any]:
    """查询指定订单的当前状态及物流信息。"""
    return order_system.query_order_status(order_id)

@tool
def create_return_request(order_id: str, reason: str, return_type: str = "退货", description: Optional[str] = None) -> Dict[str, Any]:
    """为订单创建退换货申请并返回申请详情。"""
    return order_system.create_return_request(order_id, reason, return_type, description)

@tool
def query_return_status(return_id: str) -> Dict[str, Any]:
    """查询退换货申请的处理状态。"""
    return order_system.query_return_status(return_id)

@tool
def get_all_orders(user_id: str = "U001") -> List[Dict[str, Any]]:
    """获取指定用户的全部订单列表。"""
    return order_system.get_user_orders(user_id)

@tool
def get_all_products() -> List[Dict[str, Any]]:
    """获取全部产品清单。"""
    return list(PRODUCTS_DB.values())

@tool
def update_user_preference(user_id: str, preference: str) -> str:
    """更新用户偏好设置。"""
    success = memory_manager.update_user_profile(user_id, preference)
    if success:
        return "用户偏好已更新。"
    return "更新用户偏好失败。"
