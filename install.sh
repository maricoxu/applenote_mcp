#!/bin/bash

# Apple Notes MCP Server 安装脚本
# 自动化设置虚拟环境、安装依赖、配置MCP

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo "🚀 开始安装 Apple Notes MCP Server..."

# 检查操作系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "此脚本仅支持macOS系统"
    exit 1
fi

# 获取当前目录的绝对路径
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 项目目录: $PROJECT_DIR"

# 检查必要的系统工具
echo "🔧 检查系统工具..."
if ! command -v osascript &> /dev/null; then
    print_error "未找到osascript命令，请确保在macOS系统上运行"
    exit 1
fi

if ! command -v git &> /dev/null; then
    print_warning "未找到git命令，建议安装Xcode Command Line Tools"
    echo "   运行: xcode-select --install"
fi

# 检查Python版本 - 优先使用Python 3.11+
echo "🐍 检查Python版本..."

# 尝试找到合适的Python版本
PYTHON_CMD=""
PYTHON_VERSION=""

# 检查顺序：python3.11 > python3.12 > python3.10 > python3
for cmd in python3.11 /opt/homebrew/bin/python3.11 python3.12 /opt/homebrew/bin/python3.12 python3.10 /opt/homebrew/bin/python3.10 python3; do
    if command -v "$cmd" &> /dev/null; then
        version=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "")
        if [ -n "$version" ]; then
            major=$($cmd -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "0")
            minor=$($cmd -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
            
            # 检查是否满足最低要求 (Python 3.10+)
            if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 10 ]); then
                PYTHON_CMD="$cmd"
                PYTHON_VERSION="$version"
                print_success "找到合适的Python版本: $PYTHON_VERSION ($cmd)"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    print_error "未找到Python 3.10+版本"
    echo ""
    echo "🔧 解决方案："
    echo "   请安装Python 3.11+："
    echo "   ${BLUE}brew install python@3.11${NC}"
    echo ""
    echo "   或者安装最新的Python 3："
    echo "   ${BLUE}brew install python3${NC}"
    echo ""
    echo "   如果没有Homebrew，请先安装："
    echo "   ${BLUE}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
    exit 1
fi

# 检查pip是否可用
echo "📦 检查pip..."
if ! "$PYTHON_CMD" -m pip --version &> /dev/null; then
    print_warning "pip不可用，尝试安装..."
    "$PYTHON_CMD" -m ensurepip --upgrade || {
        print_error "无法安装pip，请手动安装"
        exit 1
    }
fi

# 检查并清理损坏的虚拟环境
echo "🔍 检查虚拟环境状态..."
if [ -d ".venv" ]; then
    # 检查虚拟环境中的Python是否可用
    if [ -f ".venv/bin/python" ]; then
        if ! .venv/bin/python --version &> /dev/null; then
            print_warning "检测到损坏的虚拟环境，正在重新创建..."
            rm -rf .venv
        else
            # 检查虚拟环境的Python版本是否满足要求
            venv_version=$(.venv/bin/python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "")
            if [ -n "$venv_version" ]; then
                venv_major=$(.venv/bin/python -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo "0")
                venv_minor=$(.venv/bin/python -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo "0")
                
                if [ "$venv_major" -lt 3 ] || ([ "$venv_major" -eq 3 ] && [ "$venv_minor" -lt 10 ]); then
                    print_warning "虚拟环境Python版本过低 ($venv_version)，正在重新创建..."
                    rm -rf .venv
                else
                    print_info "虚拟环境已存在且正常 (Python $venv_version)"
                fi
            else
                print_warning "无法检测虚拟环境Python版本，正在重新创建..."
                rm -rf .venv
            fi
        fi
    else
        print_warning "虚拟环境不完整，正在重新创建..."
        rm -rf .venv
    fi
fi

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    if ! "$PYTHON_CMD" -m venv .venv; then
        print_error "虚拟环境创建失败"
        exit 1
    fi
    print_success "虚拟环境创建成功"
fi

# 验证虚拟环境
echo "🔧 验证虚拟环境..."
if ! .venv/bin/python --version &> /dev/null; then
    print_error "虚拟环境创建失败"
    exit 1
fi

VENV_PYTHON_VERSION=$(.venv/bin/python --version 2>&1)
print_success "虚拟环境Python版本: $VENV_PYTHON_VERSION"

# 检查requirements.txt文件
if [ ! -f "requirements.txt" ]; then
    print_error "未找到requirements.txt文件"
    exit 1
fi

# 激活虚拟环境并安装依赖
echo "📥 安装依赖..."
if ! .venv/bin/python -m pip install --upgrade pip; then
    print_error "pip升级失败"
    exit 1
fi

if ! .venv/bin/python -m pip install -r requirements.txt; then
    print_error "依赖安装失败"
    echo ""
    echo "🔧 可能的解决方案："
    echo "1. 检查网络连接"
    echo "2. 尝试使用国内镜像："
    echo "   ${BLUE}.venv/bin/python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/${NC}"
    exit 1
fi
print_success "依赖安装完成"

# 检查MCP服务器文件
if [ ! -f "src/mcp_server.py" ]; then
    print_error "未找到MCP服务器文件: src/mcp_server.py"
    exit 1
fi

# 测试MCP服务器
echo "🧪 测试MCP服务器..."
if [ -f "test_mcp_connection.py" ]; then
    if .venv/bin/python test_mcp_connection.py; then
        print_success "MCP服务器测试通过"
    else
        print_error "MCP服务器测试失败"
        echo ""
        echo "🔧 故障排除建议："
        echo "1. 检查AppleScript文件是否存在"
        echo "2. 确保Apple Notes应用已安装"
        echo "3. 检查系统权限设置"
        exit 1
    fi
else
    print_warning "未找到测试脚本，跳过测试"
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

print_success "配置文件模板已生成: mcp_config_template.json"

# 检查是否存在Cursor配置目录
CURSOR_CONFIG_DIR="$HOME/.cursor"
if [ -d "$CURSOR_CONFIG_DIR" ]; then
    print_info "检测到Cursor配置目录"
    
    # 备份现有配置
    if [ -f "$CURSOR_CONFIG_DIR/mcp.json" ]; then
        backup_file="$CURSOR_CONFIG_DIR/mcp.json.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CURSOR_CONFIG_DIR/mcp.json" "$backup_file"
        print_success "已备份现有配置文件到: $backup_file"
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
            # 使用Python脚本合并配置
            if .venv/bin/python << EOF
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
            then
                print_success "配置合并成功"
            else
                print_error "配置合并失败，请手动配置"
            fi
        else
            # 创建新配置文件
            cp mcp_config_template.json "$CURSOR_CONFIG_DIR/mcp.json"
            print_success "已创建新的MCP配置文件"
        fi
    else
        print_info "跳过自动配置，请手动复制配置内容"
    fi
else
    print_info "未检测到Cursor配置目录，请手动配置"
fi

echo ""
print_success "🎉 安装完成！"
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
echo ""
echo "📚 更多信息："
echo "   - 项目地址: https://github.com/maricoxu/applenote_mcp"
echo "   - 配置文件: $CURSOR_CONFIG_DIR/mcp.json"
echo "   - 虚拟环境: $PROJECT_DIR/.venv" 