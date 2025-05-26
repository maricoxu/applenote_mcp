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