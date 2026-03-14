#!/usr/bin/env python3
"""
智能电商客服系统
基于 LangChain 和 LangGraph 实现的智能客服助手
"""

import sys
import os
from app.customer_service import CustomerServiceAgent
from langchain_core.messages import HumanMessage, AIMessage


def print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("欢迎使用智能电商客服系统！")
    print("=" * 60)
    print("我可以帮您：")
    print("  1. 查询产品信息")
    print("  2. 查询订单物流状态")
    print("  3. 处理退换货申请")
    print("\n输入 'quit' 或 'exit' 退出系统")
    print("=" * 60)
    print()


def print_message(role: str, content: str):
    """打印消息"""
    if role == "user":
        print(f"\033[1;34m👤 用户:\033[0m {content}")
    elif role == "assistant":
        print(f"\033[1;32m🤖 客服:\033[0m {content}")
    print()


def main():
    """主函数"""
    # 检查配置文件
    if not os.path.exists("config.yaml"):
        print("错误：找不到 config.yaml 配置文件！")
        print("请确保配置文件存在于项目根目录。")
        sys.exit(1)
    
    # 初始化客服代理
    try:
        print("正在初始化智能客服系统...")
        agent = CustomerServiceAgent()
        print("初始化完成！\n")
    except Exception as e:
        print(f"初始化失败：{e}")
        print("请检查配置文件和网络连接。")
        sys.exit(1)
    
    # 打印欢迎信息
    print_welcome()
    
    # 对话历史
    history = []
    
    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\033[1;34m👤 用户:\033[0m ").strip()
            
            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "退出", "q"]:
                print("\n感谢使用智能电商客服系统，再见！👋")
                break
            
            # 跳过空输入
            if not user_input:
                continue
            
            # 调用客服代理
            print()
            result = agent.chat(user_input, history=history)
            
            # 更新历史
            history = result["history"]
            
            # 打印回复
            print_message("assistant", result["response"])
            
        except KeyboardInterrupt:
            print("\n\n感谢使用智能电商客服系统，再见！👋")
            break
        except Exception as e:
            print(f"\n\033[1;31m错误:\033[0m {e}\n")


if __name__ == "__main__":
    main()
