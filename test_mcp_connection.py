#!/usr/bin/env python3
"""
测试MCP服务器连接的简单脚本
"""

import subprocess
import json
import sys
import os

def test_mcp_server():
    """测试MCP服务器是否能正常启动和响应"""
    
    # MCP服务器路径
    server_path = os.path.join(os.path.dirname(__file__), "src", "mcp_server.py")
    python_path = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")
    
    print(f"Testing MCP server at: {server_path}")
    print(f"Using Python: {python_path}")
    
    try:
        # 启动MCP服务器进程
        process = subprocess.Popen(
            [python_path, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 发送初始化请求
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # 发送请求
        request_str = json.dumps(init_request) + "\n"
        print(f"Sending: {request_str.strip()}")
        
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # 读取响应（设置超时）
        import select
        import time
        
        start_time = time.time()
        timeout = 5  # 5秒超时
        
        while time.time() - start_time < timeout:
            if select.select([process.stdout], [], [], 0.1)[0]:
                response = process.stdout.readline()
                if response:
                    print(f"Received: {response.strip()}")
                    try:
                        response_data = json.loads(response)
                        if "result" in response_data:
                            print("✅ MCP服务器初始化成功!")
                            return True
                    except json.JSONDecodeError:
                        pass
            
            # 检查进程是否还在运行
            if process.poll() is not None:
                stderr_output = process.stderr.read()
                print(f"❌ 进程意外退出，错误信息: {stderr_output}")
                return False
        
        print("❌ 超时：没有收到响应")
        return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        try:
            process.terminate()
            process.wait(timeout=2)
        except:
            process.kill()

if __name__ == "__main__":
    print("🧪 开始测试MCP服务器连接...")
    success = test_mcp_server()
    sys.exit(0 if success else 1) 