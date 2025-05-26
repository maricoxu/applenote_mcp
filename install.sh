#!/bin/bash

# Apple Notes MCP Server 安装脚本
# 自动化设置虚拟环境、安装依赖、配置MCP

set -e  # 遇到错误时退出

echo "🚀 开始安装 Apple Notes MCP Server..."

# 获取当前目录的绝对路径
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 项目目录: $PROJECT_DIR"

# 检查Python版本
echo "🐍 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python版本: $PYTHON_VERSION"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "ℹ️  虚拟环境已存在"
fi

# 激活虚拟环境并安装依赖
echo "📥 安装依赖..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 依赖安装完成"

# 测试MCP服务器
echo "🧪 测试MCP服务器..."
if python test_mcp_connection.py; then
    echo "✅ MCP服务器测试通过"
else
    echo "❌ MCP服务器测试失败"
    exit 1
fi

# 生成配置文件模板
echo "⚙️  生成配置文件..."
PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
SERVER_PATH="$PROJECT_DIR/src/mcp_server.py"

cat > mcp_config_template.json << EOF
{
  "repositories": {
    "allowedDirectories": [
      "$HOME"
    ]
  },
  "mcpServers": {
    "applenote_mcp_service": {
      "command": "$PYTHON_PATH",
      "args": [
        "$SERVER_PATH"
      ],
      "disabled": false,
      "autoApprove": true
    }
  }
}
EOF

echo "✅ 配置文件模板已生成: mcp_config_template.json"

# 检查是否存在Cursor配置目录
CURSOR_CONFIG_DIR="$HOME/.cursor"
if [ -d "$CURSOR_CONFIG_DIR" ]; then
    echo "📝 检测到Cursor配置目录"
    
    # 备份现有配置
    if [ -f "$CURSOR_CONFIG_DIR/mcp.json" ]; then
        cp "$CURSOR_CONFIG_DIR/mcp.json" "$CURSOR_CONFIG_DIR/mcp.json.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✅ 已备份现有配置文件"
    fi
    
    # 询问是否自动更新配置
    echo ""
    echo "🤔 是否自动更新Cursor的MCP配置？"
    echo "   这将修改 ~/.cursor/mcp.json 文件"
    echo "   (输入 y 确认，其他键跳过)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # 如果配置文件存在，尝试合并
        if [ -f "$CURSOR_CONFIG_DIR/mcp.json" ]; then
            echo "🔄 合并现有配置..."
            # 这里可以添加更复杂的JSON合并逻辑
            # 目前简单地添加我们的服务到现有配置
            python3 << EOF
import json
import sys

try:
    # 读取现有配置
    with open('$CURSOR_CONFIG_DIR/mcp.json', 'r') as f:
        config = json.load(f)
    
    # 确保mcpServers存在
    if 'mcpServers' not in config:
        config['mcpServers'] = {}
    
    # 添加我们的服务
    config['mcpServers']['applenote_mcp_service'] = {
        "command": "$PYTHON_PATH",
        "args": ["$SERVER_PATH"],
        "disabled": False,
        "autoApprove": True
    }
    
    # 写回配置
    with open('$CURSOR_CONFIG_DIR/mcp.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ 配置已更新")
except Exception as e:
    print(f"❌ 配置更新失败: {e}")
    sys.exit(1)
EOF
        else
            # 创建新配置文件
            cp mcp_config_template.json "$CURSOR_CONFIG_DIR/mcp.json"
            echo "✅ 已创建新的MCP配置文件"
        fi
    else
        echo "⏭️  跳过自动配置，请手动复制配置内容"
    fi
else
    echo "ℹ️  未检测到Cursor配置目录，请手动配置"
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 下一步操作："
echo "1. 如果未自动配置，请将 mcp_config_template.json 的内容"
echo "   添加到 ~/.cursor/mcp.json 文件中"
echo "2. 重启Cursor IDE"
echo "3. 在Cursor中测试Apple Notes功能"
echo ""
echo "💡 使用示例："
echo '   "请帮我创建一个笔记，标题是测试，内容是Hello World"'
echo ""
echo "🔧 如果遇到问题，请查看README.md的故障排除部分" 