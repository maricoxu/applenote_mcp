#!/usr/bin/env python3
"""
AI对话文本转换工具
专门处理从AI对话界面复制的文本，转换为如流知识库友好的格式
"""

import re
from typing import List, Dict, Tuple

def clean_text(text: str) -> str:
    """清理文本中的特殊字符和多余空格"""
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除行首行尾空格
    text = text.strip()
    # 处理特殊引号
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    return text

def detect_dialogue_structure(text: str) -> List[Dict[str, str]]:
    """检测AI对话的结构，分离用户输入和AI回复"""
    
    # 常见的AI对话标识符
    user_indicators = ['用户:', '我:', '请', '帮我', '如何', '什么是', '能否']
    ai_indicators = ['AI:', '助手:', '回答:', '解答:', '建议:', '方案:']
    
    lines = text.split('\n')
    dialogue_parts = []
    current_part = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检测是否是用户输入
        is_user_input = any(indicator in line for indicator in user_indicators)
        # 检测是否是AI回复
        is_ai_reply = any(indicator in line for indicator in ai_indicators)
        
        if is_user_input and not is_ai_reply:
            # 开始新的用户输入
            if current_part:
                dialogue_parts.append(current_part)
            current_part = {
                'type': 'user',
                'content': clean_text(line)
            }
        elif current_part:
            # 继续当前部分的内容
            current_part['content'] += ' ' + clean_text(line)
        else:
            # 如果没有明确标识，默认作为内容
            if not current_part:
                current_part = {
                    'type': 'content',
                    'content': clean_text(line)
                }
            else:
                current_part['content'] += ' ' + clean_text(line)
    
    # 添加最后一个部分
    if current_part:
        dialogue_parts.append(current_part)
    
    return dialogue_parts

def extract_key_information(text: str) -> Dict[str, str]:
    """从文本中提取关键信息"""
    
    # 提取可能的标题
    title_patterns = [
        r'标题[是为]?[：:]?"?([^"]+)"?',
        r'创建.*?[：:]?"?([^"]+)"?',
        r'名称[是为]?[：:]?"?([^"]+)"?'
    ]
    
    title = ""
    for pattern in title_patterns:
        match = re.search(pattern, text)
        if match:
            title = match.group(1).strip()
            break
    
    # 提取关键词
    keywords = []
    keyword_patterns = [
        r'(项目规划|产品开发|计划|方案|策略|设计|实现)',
        r'(学习|教程|指南|文档|笔记)',
        r'(技术|编程|开发|代码|算法)'
    ]
    
    for pattern in keyword_patterns:
        matches = re.findall(pattern, text)
        keywords.extend(matches)
    
    return {
        'title': title,
        'keywords': list(set(keywords))
    }

def convert_ai_dialogue_to_ruliu_format(raw_text: str) -> str:
    """将AI对话文本转换为如流知识库友好的格式"""
    
    if not raw_text or not raw_text.strip():
        return "# 空内容\n\n请提供需要转换的AI对话文本。"
    
    # 清理输入文本
    cleaned_text = clean_text(raw_text)
    
    # 提取关键信息
    key_info = extract_key_information(cleaned_text)
    
    # 检测对话结构
    dialogue_parts = detect_dialogue_structure(cleaned_text)
    
    # 构建输出格式
    result = []
    
    # 添加标题
    if key_info['title']:
        result.append(f"# {key_info['title']}")
    else:
        result.append("# AI对话记录")
    
    result.append("")
    
    # 添加概述
    result.append("## 📋 对话概述")
    result.append("")
    
    if key_info['keywords']:
        result.append("**关键词：** " + "、".join(key_info['keywords']))
        result.append("")
    
    # 处理对话内容
    if dialogue_parts:
        result.append("## 💬 对话内容")
        result.append("")
        
        for i, part in enumerate(dialogue_parts, 1):
            if part['type'] == 'user':
                result.append(f"### {i}. 用户需求")
                result.append("")
                result.append(f"**问题：** {part['content']}")
                result.append("")
                
            elif part['type'] == 'content':
                # 尝试结构化内容
                content = part['content']
                
                # 检测是否包含步骤
                if any(keyword in content for keyword in ['步骤', '流程', '方法', '过程']):
                    result.append("**解决方案：**")
                    result.append("")
                    # 简单的步骤分解
                    sentences = content.split('。')
                    for j, sentence in enumerate(sentences, 1):
                        if sentence.strip():
                            result.append(f"{j}. {sentence.strip()}")
                    result.append("")
                    
                # 检测是否包含列表
                elif any(keyword in content for keyword in ['包括', '包含', '有以下', '如下']):
                    result.append("**详细说明：**")
                    result.append("")
                    result.append(content)
                    result.append("")
                    
                else:
                    result.append("**内容：**")
                    result.append("")
                    result.append(content)
                    result.append("")
    else:
        # 如果无法识别对话结构，直接格式化内容
        result.append("## 📝 内容详情")
        result.append("")
        result.append(cleaned_text)
        result.append("")
    
    # 添加使用建议
    result.extend([
        "---",
        "",
        "## 💡 使用建议",
        "",
        "1. **复制优化后的内容**到如流知识库",
        "2. **根据需要调整**标题和格式",
        "3. **添加标签**便于后续检索",
        "4. **关联相关文档**建立知识网络",
        "",
        "*本文档由 AI对话转换工具自动生成*"
    ])
    
    return '\n'.join(result)

def convert_simple_request_to_ruliu_format(request_text: str) -> str:
    """专门处理简单请求文本的转换"""
    
    # 清理文本
    cleaned_text = clean_text(request_text)
    
    # 提取关键信息
    key_info = extract_key_information(cleaned_text)
    
    # 构建结果
    result = []
    
    # 标题
    if key_info['title']:
        result.append(f"# {key_info['title']}")
    else:
        result.append("# 项目规划文档")
    
    result.append("")
    
    # 基本信息
    result.append("## 📋 基本信息")
    result.append("")
    result.append(f"**创建需求：** {cleaned_text}")
    result.append("")
    
    if key_info['keywords']:
        result.append(f"**关键词：** {', '.join(key_info['keywords'])}")
        result.append("")
    
    # 文档结构建议
    result.append("## 📖 建议文档结构")
    result.append("")
    
    if "项目" in cleaned_text or "计划" in cleaned_text:
        result.extend([
            "### 1. 项目概述",
            "- 项目背景",
            "- 项目目标",
            "- 预期成果",
            "",
            "### 2. 详细规划",
            "- 时间安排",
            "- 资源配置",
            "- 风险评估",
            "",
            "### 3. 执行计划",
            "- 阶段划分",
            "- 里程碑设置",
            "- 责任分工",
            "",
            "### 4. 监控与评估",
            "- 进度跟踪",
            "- 质量控制",
            "- 效果评估",
            ""
        ])
    else:
        result.extend([
            "### 1. 主要内容",
            "- 核心要点",
            "- 详细说明",
            "",
            "### 2. 相关信息",
            "- 背景资料",
            "- 参考资源",
            "",
            "### 3. 后续行动",
            "- 下一步计划",
            "- 注意事项",
            ""
        ])
    
    # 使用说明
    result.extend([
        "---",
        "",
        "## 💡 使用说明",
        "",
        "1. **完善内容**：根据上述结构填充具体内容",
        "2. **调整格式**：根据实际需要修改标题和层级",
        "3. **添加细节**：补充相关的详细信息",
        "4. **定期更新**：保持文档的时效性",
        "",
        "*本模板由 AI对话转换工具生成*"
    ])
    
    return '\n'.join(result)

# 测试函数
def test_converter():
    """测试转换功能"""
    
    # 测试用例1：简单请求
    test_text1 = "请帮我创建一个项目规划笔记，标题是'新产品开发计划'"
    
    print("=== 测试用例1：简单请求 ===")
    result1 = convert_simple_request_to_ruliu_format(test_text1)
    print(result1)
    print("\n" + "="*50 + "\n")
    
    # 测试用例2：复杂对话
    test_text2 = """
    用户: 请帮我创建一个Python学习笔记
    AI: 好的，我来帮您创建一个Python学习笔记。这个笔记应该包括基础语法、数据结构、函数定义等内容。
    建议的学习步骤包括：1. 环境搭建 2. 基础语法学习 3. 实践项目
    """
    
    print("=== 测试用例2：复杂对话 ===")
    result2 = convert_ai_dialogue_to_ruliu_format(test_text2)
    print(result2)

if __name__ == "__main__":
    test_converter()