#!/usr/bin/env python3
"""
Apple Notes MCP Server
使用官方MCP Python SDK实现的Apple Notes服务器
"""

import subprocess
import os
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

try:
    import markdown
except ImportError:
    markdown = None

# 构建 AppleScript 脚本的基础路径
BASE_APPLESCRIPT_PATH = os.path.join(os.path.dirname(__file__), "applescripts")

# 创建MCP服务器实例
mcp = FastMCP("Apple Notes MCP Server")

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

@mcp.tool()
def create_apple_note(title: str = "", content: str = "", folder: str = "", input_format: str = "text") -> dict:
    """
    在Apple Notes中创建新笔记
    
    Args:
        title: 笔记标题（可选，如果为空则自动生成）
        content: 笔记内容
        folder: 目标文件夹（可选，如果为空则使用默认文件夹）
        input_format: 输入格式，"text"或"markdown"
    
    Returns:
        包含操作结果的字典
    """
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
    
    return result

@mcp.tool()
def append_to_apple_note(title: str, content: str = "", folder: str = "", input_format: str = "text") -> dict:
    """
    向现有Apple Notes笔记追加内容
    
    Args:
        title: 要追加内容的笔记标题（必需）
        content: 要追加的内容
        folder: 笔记所在的文件夹（可选）
        input_format: 输入格式，"text"或"markdown"
    
    Returns:
        包含操作结果的字典
    """
    if not title:
        return {"status": "error", "message": "Title parameter is required for append operation."}
    
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
        return {"status": "error", "message": result["data"]["details"]}
    
    if result["status"] == "success":
        result["message"] = f"Content appended to note '{title}' successfully."
    
    return result

@mcp.tool()
def list_apple_notes(folder: str = "") -> dict:
    """
    列出Apple Notes中的笔记
    
    Args:
        folder: 要列出笔记的文件夹（可选，如果为空则列出所有笔记）
    
    Returns:
        包含笔记列表的字典
    """
    effective_folder = folder if folder else ""
    
    result = _execute_applescript("list_notes.scpt", effective_folder)
    
    if result["status"] == "success":
        raw_output = result.get("data", {}).get("details", "")
        
        if raw_output.startswith("错误：") or raw_output.startswith("信息：No notes found"):
            if "No notes found" in raw_output:
                return {"status": "success", "message": raw_output, "data": {"titles": []}}
            else:
                return {"status": "error", "message": raw_output}
        
        titles_list = raw_output.splitlines() if raw_output else []
        folder_name = effective_folder if effective_folder else 'All Notes'
        return {
            "status": "success", 
            "message": f"Successfully listed notes from folder '{folder_name}'.",
            "data": {"titles": titles_list}
        }
    
    return result

@mcp.tool()
def get_apple_note_content(title: str, folder: str = "") -> dict:
    """
    获取Apple Notes笔记的内容
    
    Args:
        title: 笔记标题（必需）
        folder: 笔记所在的文件夹（可选）
    
    Returns:
        包含笔记内容的字典
    """
    if not title:
        return {"status": "error", "message": "Title parameter is required for get content operation."}
    
    effective_folder = folder if folder else ""
    
    result = _execute_applescript("get_note_content.scpt", title, effective_folder)
    
    if result["status"] == "success":
        note_content = result.get("data", {}).get("details", "")
        
        if note_content.startswith("错误："):
            return {"status": "error", "message": note_content}
        
        return {
            "status": "success",
            "message": f"Successfully retrieved content for note '{title}'.",
            "data": {
                "title": title,
                "content": note_content,
                "folder": effective_folder
            }
        }
    
    return result

if __name__ == "__main__":
    # 运行MCP服务器
    mcp.run()