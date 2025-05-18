### 阶段 1: 核心MCP架子搭建与纯文本笔记创建 (默认文件夹)

- **目标**:
    1. 搭建一个初步的 MCP 服务层（包装脚本/函数），能够接收来自AI的创建笔记请求（如动作、内容、标题），并打印这些信息以供调试。
    2. 实现通过 AppleScript (`create_note_basic.scpt`) 创建包含纯文本内容的新笔记到苹果备忘录的默认文件夹。
    3. 将 AppleScript 的调用集成到 MCP 服务层中。
- **主要任务**:
    1.  **MCP 服务层 (初期 - 模拟)**:
        - 创建一个包装脚本/函数 (例如 `mcp_handler.py`)。 (已完成)
        - 定义接收参数：`action` (如 "create_note"), `content` (纯文本), `title` (可选)。 (已完成)
        - 实现：打印接收到的参数，模拟将要执行的动作（例如 "INFO: Would call create_note_basic.scpt..."）。 (已完成)
    2.  **AppleScript 编写 (`create_note_basic.scpt`)**:
        - 接收参数: `noteBody` (纯文本内容), `noteTitle` (可选，笔记标题)。 (已完成)
        - 功能: 在苹果备忘录的默认文件夹中创建一篇新笔记。如果提供了标题，则使用该标题。 (已完成)
        - 进行独立的 `osascript` 测试。 (已由用户确认脚本有效性)
    3.  **MCP 服务层 (集成)**:
        - 在包装脚本/函数中，当 `action == "create_note"` 时，实际通过命令行调用 `create_note_basic.scpt` 并传递参数。 (已完成)
- **可测试性**:
    - **MCP 架子测试 (初期)**: 模拟AI调用，检查打印输出是否符合预期。 (通过 `if __name__ == "__main__"` 初步模拟, `tests/test_mcp_handler.py` 提供单元测试)
    - **AppleScript 测试**: 手动通过 `osascript` 执行，检查备忘录中是否正确创建了笔记。 (已由用户确认脚本有效性)
    - **集成测试**: 模拟AI调用MCP服务层，检查备忘录中是否正确创建了笔记。 (可通过运行 `src/mcp_handler.py` 的 `if __name__ == "__main__"` 部分进行初步测试, `tests/test_mcp_handler.py` mock了subprocess调用)
- **状态**: 已完成

### 阶段 2: 支持指定文件夹、笔记标题及基础 Markdown 预处理

- **目标**:
    1.  增强 AppleScript (`create_note_advanced.scpt`) 以支持在指定的文件夹中创建笔记（如果文件夹不存在则创建），并能明确设置笔记标题。
    2.  更新 MCP 服务层 (`mcp_handler.py`) 以调用新的 AppleScript，并处理 `folder` 和 `title` 参数。
    3.  在 MCP 服务层中集成基本的 Markdown 到 HTML 的转换功能，如果请求中指定了 `input_format="markdown"` 并且 `markdown` Python 库可用。
- **主要任务**:
    1.  **AppleScript 增强 (`create_note_advanced.scpt`)**: (已完成 - 用户已提供)
        -   接收参数: `noteBody` (纯文本或HTML), `noteTitle` (笔记标题), `targetFolder` (目标文件夹名称)。
        -   功能: 如果 `targetFolder` 非空，则在该文件夹中创建/定位笔记。如果文件夹不存在，则创建它。使用 `noteTitle` 设置笔记标题。如果 `noteTitle` 为空，AppleScript 内部有逻辑处理（例如，Notes应用可能会基于内容或日期自动生成标题）。
    2.  **MCP 服务层更新 (`mcp_handler.py`)**: (已完成 - 用户已提供)
        -   修改 `handle_request` (或类似函数) 以接受 `folder` 和 `input_format` 参数。
        -   当 `action == "create_note"` 时，默认调用 `create_note_advanced.scpt`。
        -   如果 `input_format == "markdown"` 并且 `markdown` 库已安装，则在传递给 AppleScript 之前将 `content` 从 Markdown 转换为 HTML。如果库未安装或转换失败，则记录警告并使用原始内容。
        -   将 `content` (可能是HTML), `title`, 和 `folder` 参数传递给 `create_note_advanced.scpt`。
    3.  **单元测试更新 (`tests/test_mcp_handler.py`)**: (已完成 - 用户已提供)
        -   添加测试用例以验证文件夹和标题参数的正确传递。
        -   添加测试用例以验证 Markdown 转换逻辑，包括库存在、库缺失以及转换失败（如果适用）的场景。使用 `unittest.mock` 来模拟 `subprocess.run` 和 `markdown` 模块。
- **可测试性**:
    -   **本地 `mcp_handler.py` 测试**: 运行 `python src/mcp_handler.py` 会执行 `if __name__ == "__main__":` 中的预设测试场景，覆盖 Markdown、指定文件夹、空标题等情况。
    -   **单元测试**: 运行 `python -m unittest discover tests` (或 `python -m unittest tests.test_mcp_handler`) 来执行所有单元测试，这些测试会 mock 外部依赖。
    -   **实际效果验证**: 在本地测试后，检查 Apple Notes 应用以确认笔记是否按预期在正确的文件夹中创建、具有正确的标题和（转换后的）内容。
- **状态**: 已完成 (代码已实现，等待用户进行全面测试和反馈)
- **备注**: 
    - 当前标题处理逻辑为"所传即所设"。空标题由 Notes 应用根据内容自动生成。Markdown 标记（如 `#`）若在标题中，会直接作为标题的一部分显示。
    - 经过测试，在未安装 `python-markdown` 库的环境下，Markdown 内容会作为纯文本处理，符合预期。安装库后可实现 HTML 转换。

### 阶段 3: 支持笔记追加内容 (Append to Note)

- **目标**:
    1.  实现向现有笔记追加内容的功能。
    2.  需要设计 AppleScript (`append_to_note.scpt`) 来查找笔记（可能通过标题和可选的文件夹）并追加文本。
    3.  MCP 服务层增加 `append_note` 动作。
- **主要任务**:
    1.  **AppleScript 编写 (`append_to_note.scpt`)**:
        -   接收参数: `noteTitle` (或唯一标识符), `folderName` (可选), `contentToAppend` (HTML或纯文本)。
        -   功能: 查找指定笔记。如果找到，将 `contentToAppend` 追加到其现有内容的末尾。考虑如何处理笔记不存在的情况。
    2.  **MCP 服务层更新**:
        -   添加 `append_note` 动作到 `handle_request`。
        -   处理 Markdown 转换 (如果 `input_format="markdown"`)。
        -   调用 `append_to_note.scpt`。
    3.  **单元测试**.
- **状态**: 已完成
**备注**:
    - AppleScript (`append_to_note.scpt`) 实现：通过标题和可选文件夹查找笔记，找到唯一笔记则追加内容（纯文本或HTML），否则报错。
    - Python 端 (`mcp_handler.py`) 实现：添加 `append_note` 动作，处理参数及Markdown转换，调用新脚本，处理返回结果。
    - 本地集成测试验证了纯文本和Markdown（转换为HTML）的成功追加，以及对未找到笔记、空标题等错误情况的处理。
    - 修正了 `create_note_advanced.scpt` 调用时的参数顺序问题，确保了笔记标题的正确设置。

### 阶段 4: 列表笔记 (List Notes) 与读取笔记 (Read Note)

- **目标**:
    1.  实现列出特定文件夹中（或所有）笔记的标题的功能。
    2.  实现读取指定笔记内容的功能。
- **主要任务**:
    1.  **AppleScript 编写 (`list_notes.scpt`, `get_note_content.scpt`)**.
    2.  **MCP 服务层更新**.
    3.  **单元测试**.
- **状态**: 未开始

### 阶段 5: 更丰富的格式化和错误处理

- **目标**:
    1.  研究 AppleScript 对更复杂 HTML (或 RTF) 的支持程度，并尝试支持更丰富的格式（如图片、附件的引用等，如果可行）。
    2.  增强 MCP 服务层和 AppleScript 中的错误报告和处理机制。
- **状态**: 未开始

### 阶段 6: 配置与打包 (可选)

- **目标**:
    1.  如果需要，考虑将项目打包成更易于分发或作为 MCP 服务部署的形式。
    2.  外部化配置（如 AppleScript 路径等）。
- **状态**: 未开始
