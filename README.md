# applenote_mcp

## 项目目标

`applenote_mcp` 旨在设计一个机制（概念上作为MCP服务），通过该机制，AI（如Cursor内的助手）可以将文本内容（特别是AI生成的思考、笔记、代码片段等）自动化地、以用户友好的格式写入用户的苹果备忘录 (Apple Notes) 中。

核心功能包括：
- 通过 AppleScript 与苹果备忘录进行交互。
- 封装常用的备忘录操作，如创建新笔记、追加到现有笔记。
- 探索将输入文本（如Markdown）转换为苹果备忘录支持的富文本格式的方法。 

## Features
- Create new notes in Apple Notes.
- Specify target folder and title for new notes.
- Append content to existing notes (identified by title and optional folder).
- List note titles from a specific folder or all notes.
- Retrieve the content (HTML) of a specific note.
- Basic Markdown to HTML conversion for note content and appended content (requires `python-markdown` library).
- Includes helper AppleScript for deleting notes by title for easier testing and cleanup.

## MCP Integration (Conceptual)

This project can be conceptually integrated as a custom MCP (Multi-Capability Platform) service, allowing an AI assistant like Cursor to interact with Apple Notes.

### Overview

The `applenote_mcp/src/mcp_handler.py` script serves as the entry point for this service. When invoked, it expects a JSON payload describing the desired action and its parameters via standard input (stdin). It processes the request by calling the appropriate AppleScripts and then returns a JSON response via standard output (stdout).

### Communication Protocol

*   **Input (stdin)**: A JSON object specifying the action and its arguments.
    ```json
    {
        "action": "<action_name>",
        "title": "<note_title>",
        "content": "<note_content_or_content_to_append>",
        "folder": "<target_folder_name>",
        "input_format": "<text_or_markdown>"
    }
    ```
    - `action`: (string, required) One of `"create_note"`, `"append_note"`, `"list_notes"`, `"get_note_content"`.
    - `title`: (string, optional/required based on action) The title of the note.
    - `content`: (string, optional/required based on action) The content for creating or appending.
    - `folder`: (string, optional) The target folder in Apple Notes. Defaults to the main Notes account if empty or not provided.
    - `input_format`: (string, optional, defaults to "text") Specifies if the `content` is `"text"` or `"markdown"`.

*   **Output (stdout)**: A JSON object indicating the result of the operation.
    *   On success:
        ```json
        {
            "status": "success",
            "message": "Descriptive success message.",
            "data": { /* action-specific data, e.g., list of titles, note content, or details from script */ }
        }
        ```
    *   On error:
        ```json
        {
            "status": "error",
            "message": "Detailed error message."
        }
        ```

### Example Invocation (Conceptual)

An AI assistant, upon needing to create a note, would internally:
1.  Construct the JSON request:
    ```json
    {
        "action": "create_note",
        "title": "Shopping List",
        "content": "- Apples\\n- Bananas",
        "folder": "Groceries",
        "input_format": "markdown"
    }
    ```
2.  Invoke the `mcp_handler.py` script (configured in `mcp.json`), passing the JSON via stdin.
3.  Receive and parse the JSON response from stdout.

### Registering as an MCP Server in Cursor

To make this service available to Cursor, you would define it in Cursor's MCP configuration file (`~/.cursor/mcp.json`). This involves specifying how Cursor should launch and communicate with your script.

Add an entry to the `mcpServers` object in `~/.cursor/mcp.json`:

```json
{
  // ... other configurations in your mcp.json ...
  "mcpServers": {
    // ... other existing servers ...
    "applenote_mcp_service": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/YOUR/applenote_mcp/src/mcp_handler.py" 
      ],
      "disabled": false,
      "autoApprove": true 
    }
  }
}
```
**IMPORTANT**: 
1.  Replace `/ABSOLUTE/PATH/TO/YOUR/applenote_mcp/src/mcp_handler.py` with the correct absolute path to the `mcp_handler.py` script on your system.
2.  The `mcp_handler.py` script needs to be modified to:
    *   Read a single line of JSON from `sys.stdin` in its `if __name__ == "__main__":` block.
    *   Parse this JSON.
    *   Call `handle_request()` with the parsed arguments.
    *   Ensure `handle_request()` always returns a dictionary structured as described above (status, message, data/error).
    *   Print the returned dictionary as a JSON string to `sys.stdout`.
    *   All `print()` statements used for logging/debugging within `handle_request` and its helper scripts should be redirected to `sys.stderr` to avoid interfering with the JSON output on `stdout`.

This setup allows `mcp_handler.py` to function as a simple, stateless command-line service that processes one request per invocation.

## Development Notes 