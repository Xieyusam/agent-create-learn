from datetime import datetime
from typing import Dict, List, Optional
from models import Product, Order, OrderItem, ReturnRequest


class DataStore:
    """数据存储类，用于存储和管理模拟数据"""
    
    def __init__(self):
        # 产品数据
        self.products: Dict[str, Product] = {}
        # 订单数据
        self.orders: Dict[str, Order] = {}
        # 退换货申请数据
        self.return_requests: Dict[str, ReturnRequest] = {}
        
        # 初始化模拟数据
        self._init_mock_data()
    
    def _init_mock_data(self):
        """初始化模拟数据"""
        # 产品数据
        self.products = {
            "P001": Product(
                id="P001",
                name="智能手表 Pro",
                description="高端智能手表，支持心率监测、GPS定位、睡眠分析等功能",
                price=1999.0,
                category="智能穿戴",
                stock=50,
                features=["心率监测", "GPS定位", "睡眠分析", "50米防水", "14天续航"]
            ),
            "P002": Product(
                id="P002",
                name="无线蓝牙耳机",
                description="高品质无线蓝牙耳机，主动降噪，续航30小时",
                price=599.0,
                category="音频设备",
                stock=100,
                features=["主动降噪", "30小时续航", "蓝牙5.3", "触控操作", "IPX5防水"]
            ),
            "P003": Product(
                id="P003",
                name="便携充电宝 20000mAh",
                description="大容量便携充电宝，支持快充，兼容多种设备",
                price=199.0,
                category="移动电源",
                stock=200,
                features=["20000mAh容量", "22.5W快充", "多端口输出", "LED电量显示", "轻薄设计"]
            ),
            "P004": Product(
                id="P004",
                name="机械键盘 RGB",
                description="全键无冲机械键盘，RGB背光，青轴手感",
                price=399.0,
                category="电脑配件",
                stock=80,
                features=["全键无冲", "RGB背光", "青轴", "104键", "铝合金面板"]
            ),
            "P005": Product(
                id="P005",
                name="智能台灯",
                description="护眼智能台灯，支持色温调节，APP控制",
                price=299.0,
                category="智能家居",
                stock=120,
                features=["护眼LED", "色温调节", "APP控制", "定时功能", "触控开关"]
            )
        }
        
        # 订单数据
        self.orders = {
            "ORD001": Order(
                id="ORD001",
                user_id="USER001",
                items=[
                    OrderItem(product_id="P001", product_name="智能手表 Pro", quantity=1, price=1999.0),
                    OrderItem(product_id="P002", product_name="无线蓝牙耳机", quantity=2, price=599.0)
                ],
                total_amount=3197.0,
                status="delivered",
                created_at=datetime(2024, 1, 15),
                shipping_address="北京市朝阳区xxx街道xxx号",
                tracking_number="SF1234567890"
            ),
            "ORD002": Order(
                id="ORD002",
                user_id="USER001",
                items=[
                    OrderItem(product_id="P003", product_name="便携充电宝 20000mAh", quantity=1, price=199.0)
                ],
                total_amount=199.0,
                status="shipped",
                created_at=datetime(2024, 1, 20),
                shipping_address="北京市朝阳区xxx街道xxx号",
                tracking_number="YT0987654321"
            ),
            "ORD003": Order(
                id="ORD003",
                user_id="USER002",
                items=[
                    OrderItem(product_id="P004", product_name="机械键盘 RGB", quantity=1, price=399.0),
                    OrderItem(product_id="P005", product_name="智能台灯", quantity=1, price=299.0)
                ],
                total_amount=698.0,
                status="paid",
                created_at=datetime(2024, 1, 22),
                shipping_address="上海市浦东新区xxx路xxx号"
            )
        }
        
        # 退换货申请数据
        self.return_requests = {
            "RET001": ReturnRequest(
                id="RET001",
                order_id="ORD001",
                user_id="USER001",
                reason="产品质量问题",
                type="return",
                status="pending",
                created_at=datetime(2024, 1, 25),
                description="手表屏幕有划痕，影响使用"
            )
        }
    
    # 产品相关方法
    def get_product(self, product_id: str) -> Optional[Product]:
        """获取产品信息"""
        return self.products.get(product_id)
    
    def get_all_products(self) -> List[Product]:
        """获取所有产品"""
        return list(self.products.values())
    
    def search_products(self, keyword: str) -> List[Product]:
        """搜索产品"""
        keyword = keyword.lower()
        results = []
        for product in self.products.values():
            if (keyword in product.name.lower() or 
                keyword in product.description.lower() or 
                keyword in product.category.lower() or
                any(keyword in feature.lower() for feature in product.features)):
                results.append(product)
        return results
    
    # 订单相关方法
    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单信息"""
        return self.orders.get(order_id)
    
    def get_user_orders(self, user_id: str) -> List[Order]:
        """获取用户的所有订单"""
        return [order for order in self.orders.values() if order.user_id == user_id]
    
    def get_tracking_info(self, tracking_number: str) -> Dict[str, str]:
        """获取物流信息（模拟）"""
        tracking_data = {
            "SF1234567890": {
                "status": "已签收",
                "updates": [
                    "2024-01-18 14:30:00 - 快递已签收，签收人：本人",
                    "2024-01-18 09:00:00 - 快递员正在派送中",
                    "2024-01-17 18:00:00 - 快递已到达北京市朝阳区营业部",
                    "2024-01-16 12:00:00 - 快递已从深圳发出"
                ]
            },
            "YT0987654321": {
                "status": "运输中",
                "updates": [
                    "2024-01-21 15:00:00 - 快递已到达北京市转运中心",
                    "2024-01-20 20:00:00 - 快递已从上海发出",
                    "2024-01-20 14:00:00 - 商家已发货"
                ]
            }
        }
        return tracking_data.get(tracking_number, {
            "status": "未知",
            "updates": ["暂无物流信息"]
        })
    
    # 退换货相关方法
    def create_return_request(self, return_request: ReturnRequest) -> str:
        """创建退换货申请"""
        self.return_requests[return_request.id] = return_request
        return return_request.id
    
    def get_return_request(self, return_id: str) -> Optional[ReturnRequest]:
        """获取退换货申请"""
        return self.return_requests.get(return_id)
    
    def get_user_return_requests(self, user_id: str) -> List[ReturnRequest]:
        """获取用户的所有退换货申请"""
        return [req for req in self.return_requests.values() if req.user_id == user_id]


# 全局数据存储实例
data_store = DataStore()