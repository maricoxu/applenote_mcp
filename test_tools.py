#!/usr/bin/env python3
"""
测试MCP工具声明
"""
import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_handler import mcp

async def test_tools():
    """测试MCP工具"""
    try:
        tools = await mcp.list_tools()
        print("✅ MCP服务器工具列表:")
        for tool in tools:
            print(f"  📋 {tool.name}")
            print(f"     描述: {tool.description}")
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                properties = tool.inputSchema.get('properties', {})
                if properties:
                    print(f"     参数: {list(properties.keys())}")
            print()
        
        print(f"🎯 总共声明了 {len(tools)} 个工具")
        return len(tools) > 0
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tools())
    if success:
        print("✅ MCP服务器工具声明正常！")
    else:
        print("❌ MCP服务器工具声明有问题")