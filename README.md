# Apple Notes MCP Server

一个让AI助手（如Cursor）能够直接操作Apple Notes的MCP (Model Context Protocol) 服务器。

## ✨ 功能特性

- 🆕 **创建笔记** - 支持文本和Markdown格式
- 📝 **追加内容** - 向现有笔记添加内容
- 📋 **列出笔记** - 按文件夹浏览笔记
- 🔍 **获取内容** - 读取笔记的完整内容
- 📁 **文件夹支持** - 在指定文件夹中组织笔记
- 🎨 **Markdown转换** - 自动将Markdown转换为富文本

## 🚀 快速开始

### 1. 环境要求

- **macOS** (需要Apple Notes应用)
- **Python 3.11+**
- **Cursor IDE** (或其他支持MCP的AI助手)

### 2. 安装步骤

#### 方法一：一键安装（推荐）
```bash
git clone https://github.com/maricoxu/applenote_mcp.git
cd applenote_mcp
./install.sh
```

安装脚本会自动：
- 创建虚拟环境
- 安装所有依赖
- 测试MCP服务器
- 生成配置文件模板
- 可选：自动更新Cursor配置

#### 方法二：手动安装
```bash
# 克隆项目
git clone https://github.com/maricoxu/applenote_mcp.git
cd applenote_mcp

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置Cursor

#### 方法一：全局配置（推荐）
编辑 `~/.cursor/mcp.json` 文件：

```json
{
  "repositories": {
    "allowedDirectories": [
      "/Users/你的用户名"
    ]
  },
  "mcpServers": {
    "applenote_mcp_service": {
      "command": "/Users/你的用户名/path/to/applenote_mcp/.venv/bin/python",
      "args": [
        "/Users/你的用户名/path/to/applenote_mcp/src/mcp_server.py"
      ],
      "disabled": false,
      "autoApprove": true
    }
  }
}
```

**⚠️ 重要**：请将路径替换为你的实际路径！

#### 方法二：项目配置
在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "applenote_mcp_service": {
      "command": "/Users/你的用户名/path/to/applenote_mcp/.venv/bin/python",
      "args": [
        "/Users/你的用户名/path/to/applenote_mcp/src/mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

### 4. 测试安装

运行测试脚本验证安装：

```bash
python test_mcp_connection.py
```

如果看到 `✅ MCP服务器初始化成功!`，说明安装成功。

### 5. 重启Cursor

重启Cursor IDE让配置生效。

## 📖 使用方法

### 在Cursor中使用

重启Cursor后，你可以直接在对话中使用Apple Notes功能：

#### 创建笔记
```
请帮我创建一个笔记，标题是"今日任务"，内容是：
# 工作计划
- 完成项目文档
- 开会讨论需求
- 代码review
```

#### 追加内容
```
请在"今日任务"笔记中追加：
## 下午安排
- 3点：客户电话
- 4点：团队会议
```

#### 列出笔记
```
请列出我的所有笔记
```

#### 获取笔记内容
```
请显示"今日任务"笔记的内容
```

### 可用工具

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `create_apple_note` | 创建新笔记 | `title`, `content`, `folder`, `input_format` |
| `append_to_apple_note` | 追加内容 | `title`, `content`, `folder`, `input_format` |
| `list_apple_notes` | 列出笔记 | `folder` |
| `get_apple_note_content` | 获取内容 | `title`, `folder` |

### 参数说明

- **title**: 笔记标题（可选，空则自动生成）
- **content**: 笔记内容
- **folder**: 文件夹名称（可选，空则使用默认文件夹）
- **input_format**: 输入格式，`"text"` 或 `"markdown"`（默认：`"text"`）

## 🛠️ 开发和调试

### 项目结构
```
applenote_mcp/
├── src/
│   ├── mcp_server.py          # MCP服务器主文件
│   └── applescripts/          # AppleScript脚本
│       ├── create_note_advanced.scpt
│       ├── append_to_note.scpt
│       ├── list_notes.scpt
│       └── get_note_content.scpt
├── tests/                     # 单元测试
├── test_mcp_connection.py     # 连接测试脚本
├── requirements.txt           # Python依赖
└── README.md                  # 本文件
```

### 手动测试AppleScript

```bash
# 测试创建笔记
osascript src/applescripts/create_note_advanced.scpt "测试标题" "测试内容" ""

# 测试列出笔记
osascript src/applescripts/list_notes.scpt ""
```

### 调试MCP服务器

```bash
# 检查语法
python -m py_compile src/mcp_server.py

# 测试导入
python -c "import sys; sys.path.insert(0, 'src'); import mcp_server; print('OK')"

# 运行连接测试
python test_mcp_connection.py
```

## 🔧 故障排除

### 常见问题

#### 1. "Failed to create client" 错误
- 检查配置文件路径是否正确
- 确保虚拟环境路径是绝对路径
- 重启Cursor

#### 2. "osascript command not found"
- 确保在macOS系统上运行
- 检查系统PATH设置

#### 3. "Script not found" 错误
- 确保AppleScript文件存在
- 检查文件权限

#### 4. 笔记创建失败
- 确保Apple Notes应用已安装并可访问
- 检查系统权限设置

### 获取详细日志

在Cursor中查看MCP日志：
1. 打开Cursor设置
2. 查看MCP Logs面板
3. 查找错误信息

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/maricoxu/applenote_mcp.git
cd applenote_mcp

# 安装开发依赖
pip install -r requirements.txt

# 运行测试
python -m unittest discover tests/
```

## 📄 许可证

MIT License

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io/) - 提供了强大的AI工具集成框架
- [Apple Notes](https://www.apple.com/notes/) - 优秀的笔记应用
- [Cursor](https://cursor.sh/) - 智能代码编辑器

---

**💡 提示**: 如果遇到问题，请先查看[故障排除](#-故障排除)部分，或在GitHub上提交Issue。 