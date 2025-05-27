#!/usr/bin/env python3
"""
Apple Notes MCP Server
使用官方MCP Python SDK实现的Apple Notes服务器
"""

import asyncio
import subprocess
import os
import sys
from typing import Optional, Any, Sequence

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio

try:
    import markdown
except ImportError:
    markdown = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# 导入AI对话转换工具
try:
    from ai_dialogue_converter import (
        convert_ai_dialogue_to_ruliu_format,
        convert_simple_request_to_ruliu_format
    )
except ImportError:
    convert_ai_dialogue_to_ruliu_format = None
    convert_simple_request_to_ruliu_format = None

# 构建 AppleScript 脚本的基础路径
BASE_APPLESCRIPT_PATH = os.path.join(os.path.dirname(__file__), "applescripts")

# 创建MCP服务器实例
server = Server("apple-notes-mcp")

def _execute_applescript(script_name: str, *args) -> dict:
    """执行AppleScript并返回结果"""
    applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name)
    if not os.path.exists(applescript_path):
        return {"status": "error", "message": f"Script {script_name} not found."}
    
    try:
        cmd = ["osascript", applescript_path] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        script_output = result.stdout.strip()
        return {"status": "success", "message": "Operation completed successfully.", "data": {"details": script_output}}
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.strip() if e.stderr else e.stdout.strip()
        return {"status": "error", "message": f"Error executing '{script_name}': {error_output}"}
    except FileNotFoundError:
        return {"status": "error", "message": "osascript command not found."}

def _process_markdown(content: str) -> str:
    """将Markdown转换为HTML（如果可用）"""
    if markdown and content:
        try:
            return markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br'])
        except Exception:
            pass
    return content

def _convert_to_ruliu_format(html_content: str) -> str:
    """将HTML内容转换为如流知识库友好的格式（详细版）"""
    if not BeautifulSoup or not html_content:
        return html_content
    
    try:
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 转换后的文本
        result = []
        
        # 处理每个div元素
        for element in soup.find_all(['div', 'ul', 'ol', 'li']):
            text = element.get_text(strip=True)
            if not text or len(text) < 3:
                continue
                
            # 检测标题级别（基于字体大小）
            if element.find('span', style=lambda x: x and 'font-size: 24px' in x):
                # 主标题
                result.append(f"\n{'='*80}")
                result.append(f"【 {text} 】")
                result.append(f"{'='*80}\n")
                
            elif element.find('span', style=lambda x: x and 'font-size: 18px' in x):
                # 二级标题
                result.append(f"\n{'-'*60}")
                result.append(f"▶ {text}")
                result.append(f"{'-'*60}")
                
            elif element.find('b') and not element.find('font', face="Courier"):
                # 重要内容/小标题
                if "：" in text or "场景" in text or "功能" in text:
                    result.append(f"\n◆ {text}")
                else:
                    result.append(f"\n● {text}")
                    
            elif element.find('font', face="Courier"):
                # 代码块
                result.append(f"\n┌─ 代码示例 ─┐")
                for line in text.split('\n'):
                    if line.strip():
                        result.append(f"│ {line}")
                result.append(f"└─────────────┘")
                
            elif element.name == 'li':
                # 列表项
                result.append(f"  • {text}")
                
            else:
                # 普通段落
                if len(text) > 15:  # 过滤太短的文本
                    # 检查是否是特殊格式的内容
                    if "→" in text:
                        result.append(f"\n    {text}")
                    else:
                        result.append(f"\n{text}")
        
        # 清理和格式化
        formatted_text = '\n'.join(result)
        
        # 去除多余的空行
        import re
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
        
        # 添加如流知识库友好的格式
        final_result = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                            如流知识库文档                                    ║
║                        Apple Notes 内容转换                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

{formatted_text}

╔══════════════════════════════════════════════════════════════════════════════╗
║ 📋 使用说明                                                                  ║
║                                                                              ║
║ 1. 复制上述全部内容                                                         ║
║ 2. 在如流知识库中创建新文档                                                 ║
║ 3. 直接粘贴，格式已优化适配如流                                             ║
║ 4. 可根据需要调整标题层级和段落格式                                         ║
║                                                                              ║
║ 💡 提示：本文档由 Apple Notes MCP 自动转换生成                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        return final_result
        
    except Exception as e:
        return f"转换错误：{str(e)}\n\n原始内容：\n{html_content}"

def _convert_to_simple_ruliu_format(html_content: str) -> str:
    """将HTML内容转换为简洁的如流知识库格式"""
    if not BeautifulSoup or not html_content:
        return html_content
    
    try:
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取内容
        sections = []
        current_section = None
        
        # 遍历所有元素
        for element in soup.find_all(['div', 'ul', 'ol', 'li']):
            text = element.get_text(strip=True)
            if not text or len(text) < 3:
                continue
                
            # 检测主标题（24px字体）
            if element.find('span', style=lambda x: x and 'font-size: 24px' in x):
                # 这是文档标题
                title = text
                continue
                
            # 检测二级标题（18px字体或包含emoji）
            elif (element.find('span', style=lambda x: x and 'font-size: 18px' in x) or 
                  any(emoji in text for emoji in ['🎯', '🚀', '📖', '🔧', '🎉', '💡'])):
                # 开始新章节
                if current_section:
                    sections.append(current_section)
                
                # 清理标题（移除emoji和多余符号）
                import re
                clean_title = re.sub(r'[🎯🚀📖🔧🎉💡▶]', '', text).strip()
                clean_title = re.sub(r'^[：:\-\s]+', '', clean_title)
                
                current_section = {
                    'title': clean_title,
                    'content': []
                }
                
            # 检测列表项（优先处理）
            elif element.name == 'li':
                if current_section:
                    # 检查是否包含emoji和粗体内容
                    if element.find('b'):
                        # 提取emoji和粗体内容
                        emoji_match = ""
                        for emoji in ['🤔', '📝', '💔', '🔄', '✅']:
                            if emoji in text:
                                emoji_match = emoji
                                break
                        
                        # 格式化列表项
                        if emoji_match:
                            clean_text = text.replace(emoji_match, '').strip()
                            current_section['content'].append(f"- {emoji_match} **{clean_text}**")
                        else:
                            current_section['content'].append(f"- **{text}**")
                    else:
                        current_section['content'].append(f"- {text}")
                        
            # 检测重要内容（粗体）
            elif element.find('b') and not element.find('font', face="Courier"):
                if current_section:
                    # 检查是否是子标题（短文本且包含冒号）
                    if ("：" in text or "场景" in text or "思路" in text) and len(text) < 50:
                        current_section['content'].append(f"**{text}**")
                        current_section['content'].append("")  # 添加空行
                    else:
                        # 长文本作为正文，但保持粗体重点
                        if len(text) > 50:
                            # 处理包含粗体的长段落
                            current_section['content'].append(text)
                        else:
                            current_section['content'].append(f"**{text}**")
                        
            # 检测代码块
            elif element.find('font', face="Courier"):
                if current_section:
                    current_section['content'].append(f"```\n{text}\n```")
                    
            # 普通段落
            else:
                if len(text) > 15 and current_section:
                    current_section['content'].append(text)
        
        # 添加最后一个章节
        if current_section:
            sections.append(current_section)
        
        # 生成最终格式
        result = []
        
        # 文档头部
        result.append("# Apple Notes MCP 项目总结")
        result.append("")
        
        # 生成章节
        for i, section in enumerate(sections, 1):
            # 章节标题
            result.append(f"## {i}. {section['title']}")
            result.append("")
            
            # 章节内容
            for content in section['content']:
                if content.startswith('```'):
                    result.append(content)
                    result.append("")
                elif content.startswith('**') and content.endswith('**') and len(content) < 50:
                    # 短的粗体内容作为小标题
                    result.append(content)
                elif content.startswith('- '):
                    # 列表项
                    result.append(content)
                elif content == "":
                    # 保持空行
                    result.append("")
                else:
                    # 普通段落
                    result.append(content)
                    result.append("")
        
        # 添加使用说明
        result.extend([
            "---",
            "",
            "**使用说明：**",
            "1. 复制上述内容到如流知识库",
            "2. 格式已优化，可直接使用",
            "3. 支持Markdown语法高亮",
            "",
            "*本文档由 Apple Notes MCP 自动生成*"
        ])
        
        return '\n'.join(result)
        
    except Exception as e:
        return f"转换错误：{str(e)}\n\n原始内容：\n{html_content}"

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="create_apple_note",
            description="在Apple Notes中创建新笔记",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "笔记标题（可选，如果为空则自动生成）"
                    },
                    "content": {
                        "type": "string",
                        "description": "笔记内容"
                    },
                    "folder": {
                        "type": "string",
                        "description": "目标文件夹（可选，如果为空则使用默认文件夹）"
                    },
                    "input_format": {
                        "type": "string",
                        "enum": ["text", "markdown"],
                        "description": "输入格式，text或markdown",
                        "default": "text"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="append_to_apple_note",
            description="向现有Apple Notes笔记追加内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "要追加内容的笔记标题（必需）"
                    },
                    "content": {
                        "type": "string",
                        "description": "要追加的内容"
                    },
                    "folder": {
                        "type": "string",
                        "description": "笔记所在的文件夹（可选）"
                    },
                    "input_format": {
                        "type": "string",
                        "enum": ["text", "markdown"],
                        "description": "输入格式，text或markdown",
                        "default": "text"
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="list_apple_notes",
            description="列出Apple Notes中的笔记",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {
                        "type": "string",
                        "description": "要列出笔记的文件夹（可选，如果为空则列出所有笔记）"
                    }
                }
            }
        ),
        Tool(
            name="get_apple_note_content",
            description="获取Apple Notes笔记的内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "笔记标题（必需）"
                    },
                    "folder": {
                        "type": "string",
                        "description": "笔记所在的文件夹（可选）"
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="convert_note_to_ruliu_format",
            description="将Apple Notes笔记内容转换为如流知识库友好的格式",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "要转换的笔记标题（必需）"
                    },
                    "folder": {
                        "type": "string",
                        "description": "笔记所在的文件夹（可选）"
                    },
                    "format_style": {
                        "type": "string",
                        "enum": ["detailed", "simple"],
                        "description": "转换格式样式：detailed（详细格式）或 simple（简洁格式）",
                        "default": "simple"
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="convert_ai_dialogue_to_ruliu_format",
            description="将AI对话文本转换为如流知识库友好的格式",
            inputSchema={
                "type": "object",
                "properties": {
                    "dialogue_text": {
                        "type": "string",
                        "description": "AI对话文本内容（必需）"
                    },
                    "conversion_type": {
                        "type": "string",
                        "enum": ["simple", "dialogue"],
                        "description": "转换类型：simple（简单请求）或 dialogue（复杂对话）",
                        "default": "simple"
                    }
                },
                "required": ["dialogue_text"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    
    if name == "create_apple_note":
        title = arguments.get("title", "")
        content = arguments.get("content", "")
        folder = arguments.get("folder", "")
        input_format = arguments.get("input_format", "text")
        
        # 处理Markdown格式
        processed_content = content
        if input_format == "markdown":
            processed_content = _process_markdown(content)
        
        # 执行AppleScript
        effective_title = title if title else ""
        effective_folder = folder if folder else ""
        
        result = _execute_applescript("create_note_advanced.scpt", effective_title, processed_content, effective_folder)
        
        if result["status"] == "success":
            display_title = title if title else "Untitled (auto-generated)"
            result["message"] = f"Note '{display_title}' created successfully."
        
        return [TextContent(type="text", text=str(result))]
    
    elif name == "append_to_apple_note":
        title = arguments.get("title")
        content = arguments.get("content", "")
        folder = arguments.get("folder", "")
        input_format = arguments.get("input_format", "text")
        
        if not title:
            return [TextContent(type="text", text='{"status": "error", "message": "Title parameter is required for append operation."}')]
        
        # 处理Markdown格式
        processed_content = content
        if input_format == "markdown":
            processed_content = _process_markdown(content)
        
        # 执行AppleScript
        effective_folder = folder if folder else ""
        content_to_append = processed_content if processed_content is not None else ""
        
        result = _execute_applescript("append_to_note.scpt", title, effective_folder, content_to_append)
        
        # 检查AppleScript返回的错误信息
        if result["status"] == "success" and result.get("data", {}).get("details", "").startswith("错误："):
            result = {"status": "error", "message": result["data"]["details"]}
        
        if result["status"] == "success":
            result["message"] = f"Content appended to note '{title}' successfully."
        
        return [TextContent(type="text", text=str(result))]
    
    elif name == "list_apple_notes":
        folder = arguments.get("folder", "")
        effective_folder = folder if folder else ""
        
        result = _execute_applescript("list_notes.scpt", effective_folder)
        
        if result["status"] == "success":
            raw_output = result.get("data", {}).get("details", "")
            
            if raw_output.startswith("错误：") or raw_output.startswith("信息：No notes found"):
                if "No notes found" in raw_output:
                    result = {"status": "success", "message": raw_output, "data": {"titles": []}}
                else:
                    result = {"status": "error", "message": raw_output}
            else:
                titles_list = raw_output.splitlines() if raw_output else []
                folder_name = effective_folder if effective_folder else 'All Notes'
                result = {
                    "status": "success", 
                    "message": f"Successfully listed notes from folder '{folder_name}'.",
                    "data": {"titles": titles_list}
                }
        
        return [TextContent(type="text", text=str(result))]
    
    elif name == "get_apple_note_content":
        title = arguments.get("title")
        folder = arguments.get("folder", "")
        
        if not title:
            return [TextContent(type="text", text='{"status": "error", "message": "Title parameter is required for get content operation."}')]
        
        effective_folder = folder if folder else ""
        
        result = _execute_applescript("get_note_content.scpt", title, effective_folder)
        
        if result["status"] == "success":
            note_content = result.get("data", {}).get("details", "")
            
            if note_content.startswith("错误："):
                result = {"status": "error", "message": note_content}
            else:
                result = {
                    "status": "success",
                    "message": f"Successfully retrieved content for note '{title}'.",
                    "data": {
                        "title": title,
                        "content": note_content,
                        "folder": effective_folder
                    }
                }
        
        return [TextContent(type="text", text=str(result))]
    
    elif name == "convert_note_to_ruliu_format":
        title = arguments.get("title")
        folder = arguments.get("folder", "")
        format_style = arguments.get("format_style", "simple")
        
        if not title:
            return [TextContent(type="text", text='{"status": "error", "message": "Title parameter is required for conversion operation."}')]
        
        # 首先获取笔记内容
        effective_folder = folder if folder else ""
        
        result = _execute_applescript("get_note_content.scpt", title, effective_folder)
        
        if result["status"] == "success":
            note_content = result.get("data", {}).get("details", "")
            
            if note_content.startswith("错误："):
                result = {"status": "error", "message": note_content}
            else:
                # 根据格式样式选择转换函数
                if format_style == "detailed":
                    ruliu_content = _convert_to_ruliu_format(note_content)
                    format_desc = "详细格式"
                else:
                    ruliu_content = _convert_to_simple_ruliu_format(note_content)
                    format_desc = "简洁格式"
                
                result = {
                    "status": "success",
                    "message": f"Successfully converted note '{title}' to 如流 {format_desc}.",
                    "data": {
                        "title": title,
                        "original_content": note_content,
                        "ruliu_format": ruliu_content,
                        "folder": effective_folder,
                        "format_style": format_style
                    }
                }
        
        return [TextContent(type="text", text=str(result))]
    
    elif name == "convert_ai_dialogue_to_ruliu_format":
        dialogue_text = arguments.get("dialogue_text")
        conversion_type = arguments.get("conversion_type", "simple")
        
        if not dialogue_text:
            return [TextContent(type="text", text='{"status": "error", "message": "dialogue_text parameter is required for AI dialogue conversion."}')]
        
        # 检查转换工具是否可用
        if not convert_ai_dialogue_to_ruliu_format or not convert_simple_request_to_ruliu_format:
            return [TextContent(type="text", text='{"status": "error", "message": "AI dialogue conversion tools not available. Please check installation."}')]
        
        try:
            # 根据转换类型选择合适的转换函数
            if conversion_type == "dialogue":
                converted_content = convert_ai_dialogue_to_ruliu_format(dialogue_text)
                format_desc = "复杂对话格式"
            else:
                converted_content = convert_simple_request_to_ruliu_format(dialogue_text)
                format_desc = "简单请求格式"
            
            result = {
                "status": "success",
                "message": f"Successfully converted AI dialogue to 如流 {format_desc}.",
                "data": {
                    "original_text": dialogue_text,
                    "converted_content": converted_content,
                    "conversion_type": conversion_type
                }
            }
            
        except Exception as e:
            result = {
                "status": "error",
                "message": f"Error converting AI dialogue: {str(e)}"
            }
        
        return [TextContent(type="text", text=str(result))]
    
    else:
        return [TextContent(type="text", text=f'{"status": "error", "message": "Unknown tool: {name}"}')]

async def main():
    """主函数"""
    # 使用stdio传输运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 