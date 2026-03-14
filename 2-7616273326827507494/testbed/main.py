#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能电商客服系统 - 主程序
基于 LangChain 和 LangGraph 实现
"""

import sys
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from agent import agent


class ConversationManager:
    """对话管理器，用于管理对话历史和上下文"""
    
    def __init__(self):
        self.conversations: dict = {}  # user_id -> history
    
    def get_history(self, user_id: str) -> List[BaseMessage]:
        """获取用户的对话历史"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]
    
    def add_message(self, user_id: str, message: BaseMessage):
        """添加消息到对话历史"""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        self.conversations[user_id].append(message)
    
    def clear_history(self, user_id: str):
        """清除用户的对话历史"""
        if user_id in self.conversations:
            self.conversations[user_id] = []


def print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("欢迎使用智能电商客服系统！")
    print("=" * 60)
    print("我是小智，您的专属客服助手。我可以帮您：")
    print("  1. 产品咨询 - 了解我们的产品信息")
    print("  2. 订单查询 - 查看您的订单状态")
    print("  3. 物流跟踪 - 追踪您的包裹")
    print("  4. 退换货申请 - 处理退换货事宜")
    print()
    print("输入 'quit' 或 'exit' 退出系统")
    print("输入 'clear' 清除对话历史")
    print("=" * 60)
    print()


def main():
    """主函数"""
    # 初始化对话管理器
    conv_manager = ConversationManager()
    
    # 打印欢迎信息
    print_welcome()
    
    # 默认用户ID
    current_user_id = "USER001"
    
    while True:
        try:
            # 获取用户输入
            user_input = input("您: ").strip()
            
            # 处理特殊命令
            if user_input.lower() in ["quit", "exit", "退出"]:
                print("小智: 感谢您的使用，再见！")
                break
            
            if user_input.lower() in ["clear", "清除"]:
                conv_manager.clear_history(current_user_id)
                print("小智: 对话历史已清除。")
                print()
                continue
            
            if not user_input:
                continue
            
            # 获取对话历史
            history = conv_manager.get_history(current_user_id)
            
            # 调用代理进行对话
            print("小智: ", end="", flush=True)
            
            response_content = ""
            for chunk in agent.stream_chat(user_input, current_user_id, history):
                print(chunk, end="", flush=True)
                response_content += chunk
            
            print()
            print()
            
            # 更新对话历史
            conv_manager.add_message(current_user_id, HumanMessage(content=user_input))
            conv_manager.add_message(current_user_id, AIMessage(content=response_content))
            
        except KeyboardInterrupt:
            print("\n\n小智: 检测到中断，感谢您的使用，再见！")
            break
        except Exception as e:
            print(f"\n小智: 抱歉，发生了一个错误：{str(e)}")
            print("请稍后重试。")
            print()


if __name__ == "__main__":
    main()