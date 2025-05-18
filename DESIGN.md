# applenote_mcp 设计文档

## 1. 概述

本项目旨在设计并（在概念层面）实现一个 `applenote_mcp` 服务，该服务充当 AI 助手（如 Cursor）与用户本地 macOS 苹果备忘录应用之间的桥梁。核心目标是让 AI 能够方便地将内容（如讨论记录、代码片段、思考摘要等）存入用户的苹果备忘录中，并尽可能优化内容的格式以适应备忘录的富文本特性。

## 2. 核心架构与组件

该服务将主要依赖 AppleScript 来与苹果备忘录进行交互。关键组件包括：

- **AppleScript 脚本库**: 一系列 `.scpt` 文件，每个脚本负责一个特定的备忘录操作（例如，创建新笔记、查找并追加到笔记、在特定文件夹创建笔记）。这些脚本将由服务内部管理和调用。
- **服务接口 (设想中的 MCP 接口)**: 定义 AI 如何调用这些功能。例如：
  - `create_note(content: str, folder: str | None = None, title: str | None = None)`
  - `append_to_note(content: str, note_identifier: str, folder: str | None = None)`
  - `create_or_append_note(content: str, note_title: str, folder: str | None = None)`
- **文本格式化模块**: 一个前置处理模块，负责将输入文本（预期主要是 Markdown 格式）转换为苹果备忘录更易于接受的格式。

## 3. 自动化写入流程

1.  AI (Cursor) 接收用户指令，例如"将我们的讨论保存到备忘录的'项目思考'文件夹中"。
2.  AI 调用 `applenote_mcp` 服务的相应接口，传递待写入的内容、目标文件夹（可选）、笔记标题（可选）等参数。
3.  `applenote_mcp` 服务的文本格式化模块对传入的内容进行处理。
4.  服务根据接口调用选择合适的 AppleScript 脚本。
5.  通过 `osascript` 命令行工具执行该 AppleScript，将格式化后的内容传递给脚本。
6.  AppleScript 与苹果备忘录应用交互，完成笔记的创建或修改。
7.  （可选）执行结果反馈给 AI。

## 4. 富文本格式化策略

苹果备忘录支持富文本，但通过 AppleScript直接生成复杂的富文本有一定挑战。我们的策略将分阶段考虑：

- **阶段一 (基础)**: 
    - **Markdown 到 HTML**: 输入的 Markdown 文本将首先被转换为 HTML。许多现成的库可以完成此任务 (例如，Python 的 `markdown` 库)。
    - **AppleScript 与 HTML**: AppleScript 将尝试将此 HTML 设置为笔记的 `body`。苹果备忘录对 HTML 的解释能力有限，但一些基础标签（如 `<h1>-<h6>`, `<p>`, `<b>`, `<i>`, `<ul>`, `<ol>`, `<li>`, `<a>`）可能会被部分支持或以某种形式渲染。如果备忘录不直接渲染HTML，也可以考虑将HTML源码存入笔记，或提取纯文本。
    - **纯文本降级**: 如果HTML方式效果不佳或过于复杂，则首先确保纯文本的可靠写入。

- **阶段二 (增强)**:
    - **特定元素转换**: 针对常用的 Markdown 元素（如代码块、引用、表格），研究它们在苹果备忘录中是否有对应的原生富文本表示，并尝试通过 AppleScript 模拟创建这些格式。例如，代码块可能需要特殊处理，如使用固定宽度字体的纯文本或尝试通过剪贴板传递格式化的代码（这会增加复杂性）。
    - **RTF (Rich Text Format)**: 探索是否可以将内容转换为 RTF，然后通过某种方式（可能涉及剪贴板或临时文件）导入备忘录。RTF 是一种更传统的富文本格式，macOS 对其有较好的原生支持。
    - **利用"服务"菜单或快捷指令**: 如果 AppleScript 直接操作有困难，可以考虑编写一个接收文本的 macOS 服务或快捷指令，该服务/快捷指令内部进行富文本处理并创建笔记，然后 AppleScript 仅负责调用此服务/快捷指令。这增加了用户配置的复杂性，但可能提供更好的富文本效果。

- **核心原则**: 
    - **优雅降级**: 富文本处理失败时不应影响核心的文本写入功能。
    - **简单优先**: 从最简单可靠的纯文本或基础HTML开始，逐步增强。

## 5. AppleScript 示例 (概念)

```applescript
-- create_new_note.scpt
on run {noteBody, noteTitle, targetFolder}
    tell application "Notes"
        activate
        if targetFolder is not ""
            if not (exists folder targetFolder)
                make new folder with properties {name:targetFolder}
            end if
            set container to folder targetFolder
        else
            set container to default folder
        end if

        if noteTitle is not ""
            make new note at container with properties {name:noteTitle, body:noteBody}
        else
            make new note at container with properties {body:noteBody}
        end if
    end tell
end run
```

## 6. 未来展望

- 支持图片、附件等（通过 AppleScript 操作这类内容会更复杂）。
- 与其他 macOS 应用（如日历、提醒事项）的联动。
- 提供一个简单的命令行工具，方便用户直接在终端使用这些脚本。 