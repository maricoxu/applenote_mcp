'''import subprocess
import os
import json
import sys

try:
    import markdown
except ImportError:
    markdown = None # 如果没有安装markdown库，则标记为None

# 构建 AppleScript 脚本的基础路径
BASE_APPLESCRIPT_PATH = os.path.join(os.path.dirname(__file__), "applescripts")

def handle_request(action: str, content: str, title: str = None, folder: str = None, script_name: str = None, input_format: str = "text"):
    """
    MCP服务层处理器。
    input_format: "text" or "markdown" (用于决定是否进行转换)
    """
    print("--- MCP Request Received ---", file=sys.stderr)
    print(f"Action: {action}", file=sys.stderr)
    print(f"Input Format: {input_format}", file=sys.stderr)
    if action == "append_note":
        print(f"Content to Append: '{content[:100]}...'" if content else "Content to Append: [EMPTY]", file=sys.stderr)
    else:
        print(f"Raw Content: '{content[:100]}...'" if content else "Raw Content: [EMPTY]", file=sys.stderr)
    if title:
        print(f"Title: '{title}'", file=sys.stderr)
    if folder:
        print(f"Folder: '{folder}'", file=sys.stderr)
    print("--- End of MCP Request ---", file=sys.stderr)

    processed_content = content
    if input_format == "markdown" and action in ["create_note", "append_note"]:
        if markdown:
            try:
                processed_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br'])
                print(f"INFO: Content converted from Markdown to HTML (with nl2br): '{processed_content[:100]}...'" if processed_content else "INFO: Content converted from Markdown to HTML: [EMPTY]", file=sys.stderr)
            except Exception as e:
                print(f"WARN: Markdown to HTML conversion failed: {e}. Using raw content.", file=sys.stderr)
        else:
            print("WARN: `markdown` library not installed. Cannot convert Markdown to HTML. Using raw content.", file=sys.stderr)

    if action == "create_note":
        script_name_to_use = "create_note_advanced.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)
        if not os.path.exists(applescript_path):
            return {"status": "error", "message": f"Script {script_name_to_use} not found."}
        else:
            try:
                effective_title = title if title else ""
                effective_folder = folder if folder else ""
                cmd = ["osascript", applescript_path, effective_title, processed_content, effective_folder]
                print(f"INFO: Executing AppleScript: {' '.join(cmd)}", file=sys.stderr)
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                script_output = result.stdout.strip()
                print(f"SUCCESS: AppleScript executed. Output: {script_output}", file=sys.stderr)
                display_title = title if title else "Untitled (auto-generated)"
                return {"status": "success", "message": f"Note '{display_title}' processed (created).", "data": {"details": script_output}}
            except subprocess.CalledProcessError as e:
                error_output = e.stderr.strip() if e.stderr else e.stdout.strip()
                print(f"ERROR: AppleScript execution failed for '{script_name_to_use}'. Return code: {e.returncode}. Output: {error_output}", file=sys.stderr)
                return {"status": "error", "message": f"Error executing '{script_name_to_use}': {error_output}"}
            except FileNotFoundError:
                print(f"ERROR: osascript command not found. Please ensure it is in your PATH.", file=sys.stderr)
                return {"status": "error", "message": "osascript command not found."}
    elif action == "append_note":
        if not title:
            return {"status": "error", "message": "Title parameter is required for append_note action."}
        content_to_append = processed_content if processed_content is not None else ""
        script_name_to_use = "append_to_note.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)
        if not os.path.exists(applescript_path):
            return {"status": "error", "message": f"Script {script_name_to_use} not found."}
        else:
            try:
                effective_folder = folder if folder else ""
                cmd = ["osascript", applescript_path, title, effective_folder, content_to_append]
                print(f"INFO: Executing AppleScript: {' '.join(cmd)}", file=sys.stderr)
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                script_output = result.stdout.strip()
                print(f"SUCCESS: AppleScript executed. Output: {script_output}", file=sys.stderr)
                if script_output.startswith("错误："):
                    print(f"INFO: AppleScript reported an issue for append: {script_output}", file=sys.stderr)
                    return {"status": "error", "message": script_output}    
                return {"status": "success", "message": f"Note '{title}' processed (appended).", "data": {"details": script_output}}
            except subprocess.CalledProcessError as e:
                raw_stdout = e.stdout.strip()
                if raw_stdout.startswith("错误："):
                    print(f"INFO: AppleScript reported an issue for '{script_name_to_use}': {raw_stdout}", file=sys.stderr)
                    return {"status": "error", "message": raw_stdout}
                else:
                    error_output = e.stderr.strip() if e.stderr else raw_stdout
                    print(f"ERROR: AppleScript execution failed for '{script_name_to_use}'. Return code: {e.returncode}. Output: {error_output}", file=sys.stderr)
                    return {"status": "error", "message": f"Error executing '{script_name_to_use}': {error_output}"}
            except FileNotFoundError:
                print(f"ERROR: osascript command not found. Please ensure it is in your PATH.", file=sys.stderr)
                return {"status": "error", "message": "osascript command not found."}
    elif action == "list_notes":
        script_name_to_use = "list_notes.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)
        if not os.path.exists(applescript_path):
            return {"status": "error", "message": f"Script {script_name_to_use} not found."}
        effective_folder = folder if folder else ""
        try:
            cmd = ["osascript", applescript_path, effective_folder]
            print(f"INFO: Executing AppleScript: {' '.join(cmd)}", file=sys.stderr)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            raw_output = result.stdout.strip()
            print(f"SUCCESS: AppleScript executed for list_notes. Raw Output: {raw_output[:200]}...", file=sys.stderr)
            if raw_output.startswith("错误：") or raw_output.startswith("信息：No notes found"):
                 return {"status": "success", "message": raw_output, "data": {"titles": [] if "No notes found" in raw_output else None}}
            titles_list = raw_output.splitlines()
            return {"status": "success", "message": f"Successfully listed notes from folder '{effective_folder if effective_folder else 'All Notes'}'." , "data": {"titles": titles_list}}
        except subprocess.CalledProcessError as e:
            raw_stdout = e.stdout.strip()
            if raw_stdout.startswith("错误：") or raw_stdout.startswith("信息："):
                return {"status": "error", "message": raw_stdout}
            else:
                error_output = e.stderr.strip() if e.stderr else raw_stdout
                return {"status": "error", "message": f"Error executing '{script_name_to_use}': {error_output}"}
        except FileNotFoundError:
            return {"status": "error", "message": f"{script_name_to_use} command not found."}
    elif action == "get_note_content":
        if not title:
            return {"status": "error", "message": "Title parameter is required for get_note_content action."}
        script_name_to_use = "get_note_content.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)
        if not os.path.exists(applescript_path):
            return {"status": "error", "message": f"Script {script_name_to_use} not found."}
        effective_folder = folder if folder else ""
        try:
            cmd = ["osascript", applescript_path, title, effective_folder]
            print(f"INFO: Executing AppleScript: {' '.join(cmd)}", file=sys.stderr)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            note_content = result.stdout.strip()
            print(f"SUCCESS: AppleScript executed for get_note_content. Output: {note_content[:200]}...", file=sys.stderr)
            if note_content.startswith("错误："):
                return {"status": "error", "message": note_content}
            return {"status": "success", "message": f"Successfully retrieved content for note '{title}'.", "data": {"title": title, "content": note_content, "folder": effective_folder}}
        except subprocess.CalledProcessError as e:
            raw_stdout = e.stdout.strip()
            if raw_stdout.startswith("错误："):
                return {"status": "error", "message": raw_stdout}
            else:
                error_output = e.stderr.strip() if e.stderr else raw_stdout
                return {"status": "error", "message": f"Error executing '{script_name_to_use}': {error_output}"}
        except FileNotFoundError:
             return {"status": "error", "message": f"{script_name_to_use} command not found."}
    else:
        print(f"WARN: Action '{action}' is not recognized.", file=sys.stderr)
        return {"status": "error", "message": f"Action '{action}' not recognized."}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run-tests":
        # --- Test Suite Mode ---
        print("--- Running Test Suite --- ", file=sys.stderr)
        initial_global_markdown_module_state = None
        if 'markdown' in globals() and globals()['markdown'] is not None:
            initial_global_markdown_module_state = markdown
        elif markdown is None:
            pass 
        else: 
            print("WARN: Initial global markdown module state is indeterminate before test suite!", file=sys.stderr)

        def cleanup_note(title_to_delete, folder_name):
            print(f"--- Attempting to delete note '{title_to_delete}' from folder '{folder_name}' ---", file=sys.stderr)
            script_path = os.path.join(BASE_APPLESCRIPT_PATH, "delete_note_by_title.scpt")
            if not os.path.exists(script_path):
                print(f"WARN: Cleanup script 'delete_note_by_title.scpt' not found at {script_path}", file=sys.stderr)
                return "Error: delete_note_by_title.scpt not found."
            try:
                cmd = ["osascript", script_path, title_to_delete, folder_name]
                result = subprocess.run(cmd, capture_output=True, text=True, check=False) 
                output = result.stdout.strip() if result.stdout else ""
                if result.stderr.strip():
                    output += " STDERR: " + result.stderr.strip()
                print(f"Cleanup result for '{title_to_delete}' (in {folder_name if folder_name else 'default'}): {output}", file=sys.stderr)
                return output
            except Exception as e:
                print(f"Exception during cleanup of '{title_to_delete}': {e}", file=sys.stderr)
                return f"Exception during cleanup: {e}"

        print("--- Full Test Suite for MCP Handler ---", file=sys.stderr)

        # Test variables (consistent indentation for this block - 8 spaces from margin)
        focused_test_folder = "MCP Tests"
        focused_target_title = "Append Test Target S3"
        focused_initial_content = "Initial content for focused append test."
        focused_append_text = " This is focused appended plain text."
        focused_append_md = "## Appended Section\\n* Item A\\n* Item B" 
        mistitled_cleanup_target = "Initial content for append test."
        
        sample_markdown_text = """# Markdown Header
        **Bold Text** and *Italic Text*.
        - Item 1
        - Item 2
        ```python
        def hello():
            print("Hello, Markdown!")
        ```
"""

        print("\n--- Global Initial Cleanup Phase ---", file=sys.stderr)
        # Consistently 8-space indented cleanup_note calls
        cleanup_note(focused_target_title, focused_test_folder)
        cleanup_note(mistitled_cleanup_target, focused_test_folder)
        cleanup_note("Markdown Test Note S2", focused_test_folder)
        cleanup_note("Plain Text Default S2", "") # This was the IndentationError line
        cleanup_note("MD Fallback Test S2", focused_test_folder)
        cleanup_note("Note with ' \" \\ & < > 测试标题特殊字符", focused_test_folder)
        cleanup_note("Target for Special Append C2", focused_test_folder)
        cleanup_note("Note in Special Folder C3", "Special Folder ' \" \\ & < > 测试文件夹")
        cleanup_note("Empty Content Test Note S5.3.1 PT", focused_test_folder)
        cleanup_note("Empty Content Test Note S5.3.1 MD", focused_test_folder)
        cleanup_note("Large Content Plain Text Test Note S5.3.2", focused_test_folder)
        cleanup_note("Large Content Markdown Test Note S5.3.3", focused_test_folder)
        cleanup_note("Target for Empty Append S5.3.4", focused_test_folder)
        cleanup_note("Target for Large Append Plain Text S5.3.5", focused_test_folder)
        cleanup_note("Target for Large Append Markdown S5.3.6", focused_test_folder)

        # --- Section A: Focused Create, List, Get, Append Tests ---
        print("\n--- Section A: Focused Create, List, Get, Append Tests ---", file=sys.stderr)
        print(f"\n--- A.1. Create '{focused_target_title}' ---", file=sys.stderr)
        create_response_A1 = handle_request(action="create_note", content=focused_initial_content, title=focused_target_title, folder=focused_test_folder, input_format="text")
        print(f"Create Response (A.1): {create_response_A1}", file=sys.stderr)
        
        print(f"\n--- A.2. List notes in '{focused_test_folder}' after A.1 creation ---", file=sys.stderr)
        list_response_A2 = handle_request(action="list_notes", content=None, title=None, folder=focused_test_folder)
        print(f"List Response (A.2): {list_response_A2}", file=sys.stderr)
        if isinstance(list_response_A2, dict) and list_response_A2.get("status") == "success":
            titles_A2 = list_response_A2.get('data', {}).get('titles', [])
            print(f"Notes found (A.2): {titles_A2}", file=sys.stderr)
            count_A2 = titles_A2.count(focused_target_title)
            print(f"Occurrences of '{focused_target_title}' (A.2): {count_A2}", file=sys.stderr)
            if count_A2 != 1: print(f"WARNING (A.2): Expected 1 occurrence of '{focused_target_title}' but found {count_A2}.", file=sys.stderr)
            if mistitled_cleanup_target in titles_A2 : print(f"WARNING (A.2): A note titled with initial content '{mistitled_cleanup_target}' was also found!\\", file=sys.stderr)

        print(f"\n--- A.3. Get content of '{focused_target_title}' ---", file=sys.stderr)
        get_response_A3 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
        print(f"Get Content Response (A.3): {get_response_A3}", file=sys.stderr)
        if isinstance(get_response_A3, dict) and get_response_A3.get("status") == "success": print(f"Retrieved content (A.3): {get_response_A3.get('data',{}).get('content')}", file=sys.stderr)

        print(f"\n--- A.4. Append text to '{focused_target_title}' ---", file=sys.stderr)
        append_text_response_A4 = handle_request(action="append_note", content=focused_append_text, title=focused_target_title, folder=focused_test_folder, input_format="text")
        print(f"Append Text Response (A.4): {append_text_response_A4}", file=sys.stderr)

        print(f"\n--- A.5. Get content of '{focused_target_title}' after text append ---", file=sys.stderr)
        get_response_A5 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
        print(f"Get Content Response (A.5): {get_response_A5}", file=sys.stderr)
        if isinstance(get_response_A5, dict) and get_response_A5.get("status") == "success":
            retrieved_content_A5 = get_response_A5.get('data',{}).get('content','')
            print(f"Retrieved content (A.5): {retrieved_content_A5}", file=sys.stderr)
            if focused_initial_content in retrieved_content_A5 and focused_append_text.strip() in retrieved_content_A5: print("Content after text append (A.5) seems correct.", file=sys.stderr)
            else: print("WARNING (A.5): Content after text append might be incorrect.", file=sys.stderr)

        print(f"\n--- A.6. Append Markdown to '{focused_target_title}' ---", file=sys.stderr)
        current_markdown_temp_A6 = markdown
        if 'markdown' not in globals() or markdown is None:
            if initial_global_markdown_module_state is not None: markdown = initial_global_markdown_module_state
            else: 
                try: import markdown as md_lib_A6; markdown = md_lib_A6
                except ImportError: markdown = None
        append_md_response_A6 = handle_request(action="append_note", content=focused_append_md, title=focused_target_title, folder=focused_test_folder, input_format="markdown")
        print(f"Append MD Response (A.6): {append_md_response_A6}", file=sys.stderr)
        markdown = current_markdown_temp_A6 

        print(f"\n--- A.7. Get content of '{focused_target_title}' after MD append ---", file=sys.stderr)
        get_response_A7 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
        print(f"Get Content Response (A.7): {get_response_A7}", file=sys.stderr)
        if isinstance(get_response_A7, dict) and get_response_A7.get("status") == "success":
            retrieved_content_A7 = get_response_A7.get('data',{}).get('content', '')
            print(f"Retrieved content (A.7): {retrieved_content_A7}", file=sys.stderr)
            all_present_A7 = focused_initial_content in retrieved_content_A7 and "Appended Section" in retrieved_content_A7 and "Item A" in retrieved_content_A7 and "Item B" in retrieved_content_A7
            if all_present_A7: print("Content after MD append (A.7) seems correct.", file=sys.stderr)
            else: print("WARNING (A.7): Content after MD append might be incorrect.", file=sys.stderr)


        print("\n\n--- Section B: Adapted Original Test Suite ---", file=sys.stderr)
        print("\n--- Test B.1 (Create): Create 'Markdown Test Note S2' ---", file=sys.stderr)
        md_content_B1 = """# My Markdown Note\\n\\nThis is a *test* with [a link](http://example.com) and some `code`.\\n\\n- Item 1\\n- Item 2"""
        handle_request(action="create_note", content=md_content_B1, title="Markdown Test Note S2", folder=focused_test_folder, input_format="markdown")
        print("---------------------------------", file=sys.stderr)

        print("\n--- Test B.2 (Create): Create 'Plain Text Default S2' in default folder ---", file=sys.stderr)
        text_content_B2 = "This is a plain text note for the default folder."
        handle_request(action="create_note", content=text_content_B2, title="Plain Text Default S2", folder="", input_format="text")

        print("\n--- Test B.3 (Create): Create 'MD Fallback Test S2' (simulating missing markdown lib) ---", file=sys.stderr)
        current_markdown_temp_B3 = markdown 
        markdown = None 
        print(f"DEBUG: markdown module set to None for Test B.3", file=sys.stderr)
        handle_request(action="create_note", content="# Test MD Fallback\\nThis should be plain.", title="MD Fallback Test S2", folder=focused_test_folder, input_format="markdown")
        markdown = current_markdown_temp_B3 
        print(f"DEBUG: markdown module restored for Test B.3", file=sys.stderr)
        
        print("\n--- Test B.4 (Create): Create note with an empty title ---", file=sys.stderr)
        cleanup_note("", focused_test_folder) 
        handle_request(action="create_note", content="Content for note with empty title for stage 2.", title="", folder=focused_test_folder, input_format="text")
        print("---------------------------------", file=sys.stderr)

        print("\n--- Test B.5 (Append): Append plain text to 'Append Test Target S3' (again) ---", file=sys.stderr)
        handle_request(action="append_note", content=" This is a second plain text append (Test B.5).", title=focused_target_title, folder=focused_test_folder, input_format="text")

        print(f"\n--- Test B.6 (Append): Append Markdown to '{focused_target_title}' (again) ---", file=sys.stderr)
        appended_md_content_B6 = "### Another MD Section\\n1. One\\n2. Two"
        current_markdown_temp_B6 = markdown
        if 'markdown' not in globals() or markdown is None: 
            if initial_global_markdown_module_state is not None: markdown = initial_global_markdown_module_state
            else: 
                try: import markdown as md_lib_B6; markdown = md_lib_B6
                except ImportError: markdown = None
        handle_request(action="append_note", content=appended_md_content_B6, title=focused_target_title, folder=focused_test_folder, input_format="markdown")
        markdown = current_markdown_temp_B6

        print("\n--- Test B.7 (Append): Attempt to append to a non-existent note ---", file=sys.stderr)
        cleanup_note("NonExistent Note For Append B7", focused_test_folder)
        handle_request(action="append_note", content="This should fail.", title="NonExistent Note For Append B7", folder=focused_test_folder, input_format="text")

        print("\n--- Test B.8 (Append): Attempt to append with an empty title ---", file=sys.stderr)
        handle_request(action="append_note", content="This should fail due to no title.", title="", folder=focused_test_folder, input_format="text")

        print("\n--- Test B.9 (Append): Placeholder for testing append to multiple notes (manual setup) ---", file=sys.stderr)
        print("(Skipping Test B.9 - requires manual creation of duplicate notes in 'MCP Tests' folder named 'Duplicate Name Note')", file=sys.stderr)

        print("\n--- Test B.10 (List): List notes from 'MCP Tests' folder (end of suite) ---", file=sys.stderr)
        list_result_B10 = handle_request(action="list_notes", content=None, title=None, folder=focused_test_folder)
        print(f"List MCP Tests Result (B.10): {list_result_B10}", file=sys.stderr)

        print("\n--- Test B.11 (List): List notes from all notes (default folder, end of suite) ---", file=sys.stderr)
        list_result_B11 = handle_request(action="list_notes", content=None, title=None, folder="") 
        print(f"List All Notes Result (B.11): {list_result_B11}", file=sys.stderr)

        print("\n--- Test B.12 (Get Content): Get final content of 'Append Test Target S3' ---", file=sys.stderr)
        get_content_result_B12 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
        print(f"Get Final Content Result for '{focused_target_title}' (B.12): {get_content_result_B12}", file=sys.stderr)
        if isinstance(get_content_result_B12, dict) and get_content_result_B12.get("status") == "success":
            final_content_B12 = get_content_result_B12.get('data',{}).get('content', '')
            # Corrected multi-line if by wrapping condition in parentheses
            if (focused_initial_content in final_content_B12 and
                focused_append_text.strip() in final_content_B12 and
                "Appended Section" in final_content_B12 and "Item A" in final_content_B12 and
                "This is a second plain text append (Test B.5)." in final_content_B12 and
                "Another MD Section" in final_content_B12 and "One" in final_content_B12):
                print("Final content of 'Append Test Target S3' (B.12) seems correct with all appends.", file=sys.stderr)
            else:
                print("WARNING (B.12): Final content of 'Append Test Target S3' might be missing some parts.", file=sys.stderr)

        print("\n--- Test B.13 (Get Content): Attempt to get content of a non-existent note ---", file=sys.stderr)
        cleanup_note("NonExistent Note For GetContent B13", focused_test_folder)
        get_content_non_existent_B13 = handle_request(action="get_note_content", content=None, title="NonExistent Note For GetContent B13", folder=focused_test_folder)
        print(f"Get Content Non-Existent Result (B.13): {get_content_non_existent_B13}", file=sys.stderr)

        print("\n--- Test B.14 (List): List notes from a non-existent folder ---", file=sys.stderr)
        list_non_existent_folder_B14 = handle_request(action="list_notes", content=None, title=None, folder="FolderThatDoesNotExist_B14")
        print(f"List Non-Existent Folder Result (B.14): {list_non_existent_folder_B14}", file=sys.stderr)

        print("\n\n--- Section C: Tests for Special Characters and Content Handling ---", file=sys.stderr)
        special_char_title_C1 = "Note with ' \" \\ & < > 测试标题特殊字符"
        special_char_content_md_C1 = (
            "## Content with Special Chars: ' \" \\ & < > emojis 😊✨\\n"
            "This is a line.\\n"
            "This is another line needing nl2br.\\n\\n" 
            "- List item one\\n"
            "- List item *two* with specials: ' \" \\ & < >\\n"
            "```python\\n"
            "print(\"Hello with ' \\\\ \" & < >\")\\n" 
            "# Comment with specials ' \" \\ & < >\\n"
            "```"
        )
        print(f"\n--- Test C.1: Create '{special_char_title_C1}' with special Markdown content ---", file=sys.stderr)
        create_response_C1 = handle_request(action="create_note", title=special_char_title_C1, content=special_char_content_md_C1, folder=focused_test_folder, input_format="markdown")
        print(f"Create Response (C.1): {create_response_C1}", file=sys.stderr)
        if isinstance(create_response_C1, dict) and create_response_C1.get("status") == "success":
            print(f"\n--- Test C.1 Verification: List and Get '{special_char_title_C1}' ---", file=sys.stderr)
            list_response_C1_verify = handle_request(action="list_notes",content=None, title=None, folder=focused_test_folder)
            found_C1 = False
            if isinstance(list_response_C1_verify, dict) and list_response_C1_verify.get("status") == "success":
                titles_C1 = list_response_C1_verify.get('data', {}).get('titles', [])
                if special_char_title_C1 in titles_C1: found_C1 = True; print(f"SUCCESS (C.1 List Verify): Note '{special_char_title_C1}' found.", file=sys.stderr)
                else: print(f"WARNING (C.1 List Verify): Note '{special_char_title_C1}' NOT found in list: {titles_C1}", file=sys.stderr)
            if found_C1:
                get_response_C1_verify = handle_request(action="get_note_content", content=None, title=special_char_title_C1, folder=focused_test_folder)
                print(f"Get Content Response (C.1 Verify): {get_response_C1_verify}", file=sys.stderr)
                if isinstance(get_response_C1_verify, dict) and get_response_C1_verify.get("status") == "success":
                    retrieved_content_C1 = get_response_C1_verify.get('data', {}).get('content', '')
                    if "Content with Special Chars: ' \" \\ &amp; &lt; &gt; emojis 😊✨" in retrieved_content_C1 and "Hello with ' \\\\ \" & < >" in retrieved_content_C1 : print("SUCCESS (C.1 Get Verify): Key special phrases found.", file=sys.stderr)
                    else: print(f"WARNING (C.1 Get Verify): Retrieved content for '{special_char_title_C1}' mismatch.", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        target_title_C2 = "Target for Special Append C2"
        initial_content_C2 = "Initial simple content for C2."
        append_text_special_C2 = " Appended plain text with ' \" \\ & < > 😊✨"
        append_md_special_C2 = ("### Appended MD Section with Specials\\n" "> Quote with ' \" \\ & < >\\n" "And some `inline_code_with_specials('\"\\\\&<>\')`")
        print(f"\n--- Test C.2 Setup: Create '{target_title_C2}' ---", file=sys.stderr)
        handle_request(action="create_note", title=target_title_C2, content=initial_content_C2, folder=focused_test_folder, input_format="text")
        print(f"\n--- Test C.2.1: Append plain text with special chars to '{target_title_C2}' ---", file=sys.stderr)
        append_response_C2_1 = handle_request(action="append_note", title=target_title_C2, content=append_text_special_C2, folder=focused_test_folder, input_format="text")
        print(f"Append Response (C.2.1): {append_response_C2_1}", file=sys.stderr)
        print(f"\n--- Test C.2.2: Append Markdown with special chars to '{target_title_C2}' ---", file=sys.stderr)
        append_response_C2_2 = handle_request(action="append_note", title=target_title_C2, content=append_md_special_C2, folder=focused_test_folder, input_format="markdown")
        print(f"Append Response (C.2.2): {append_response_C2_2}", file=sys.stderr)
        print(f"\n--- Test C.2 Verification: Get content of '{target_title_C2}' after appends ---", file=sys.stderr)
        get_response_C2_verify = handle_request(action="get_note_content", content=None, title=target_title_C2, folder=focused_test_folder)
        print(f"Get Content Response (C.2 Verify): {get_response_C2_verify}", file=sys.stderr)
        if isinstance(get_response_C2_verify, dict) and get_response_C2_verify.get("status") == "success":
            retrieved_content_C2 = get_response_C2_verify.get('data', {}).get('content', '')
            text_ok = "Appended plain text with ' \" \\ &amp; &lt; &gt; 😊✨" in retrieved_content_C2
            md_ok = "Appended MD Section with Specials" in retrieved_content_C2 and "Quote with ' \" \\ &amp; &lt; &gt;" in retrieved_content_C2 and "inline_code_with_specials('\"\\\\&amp;&lt;&gt;')" in retrieved_content_C2
            if initial_content_C2 in retrieved_content_C2 and text_ok and md_ok: print("SUCCESS (C.2 Get Verify): Key phrases from special appends found.", file=sys.stderr)
            else: print(f"WARNING (C.2 Get Verify): Retrieved content for '{target_title_C2}' missing special appends.", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        special_folder_name_C3 = "Special Folder ' \" \\ & < > 测试文件夹"
        note_title_in_special_folder_C3 = "Note in Special Folder C3"
        note_content_C3 = "Content for note in a folder with special name."
        print(f"\n--- Test C.3.1: Create note '{note_title_in_special_folder_C3}' in special folder '{special_folder_name_C3}' ---", file=sys.stderr)
        create_response_C3 = handle_request(action="create_note", title=note_title_in_special_folder_C3, content=note_content_C3, folder=special_folder_name_C3, input_format="text")
        print(f"Create Response (C.3.1): {create_response_C3}", file=sys.stderr)
        if isinstance(create_response_C3, dict) and create_response_C3.get("status") == "success":
            print(f"\n--- Test C.3.2 Verification: List notes from special folder '{special_folder_name_C3}' ---", file=sys.stderr)
            list_response_C3_verify = handle_request(action="list_notes", content=None,title=None, folder=special_folder_name_C3)
            print(f"List Response (C.3.2): {list_response_C3_verify}", file=sys.stderr)
            found_in_list_C3 = False
            if isinstance(list_response_C3_verify, dict) and list_response_C3_verify.get("status") == "success":
                titles_C3 = list_response_C3_verify.get('data', {}).get('titles', [])
                if note_title_in_special_folder_C3 in titles_C3: found_in_list_C3 = True; print(f"SUCCESS (C.3.2 List Verify): Note '{note_title_in_special_folder_C3}' found in special folder.", file=sys.stderr)
                else: print(f"WARNING (C.3.2 List Verify): Note '{note_title_in_special_folder_C3}' NOT found in special folder list: {titles_C3}", file=sys.stderr)
            if found_in_list_C3:
                print(f"\n--- Test C.3.3 Verification: Get content of '{note_title_in_special_folder_C3}' from special folder ---", file=sys.stderr)
                get_response_C3_verify = handle_request(action="get_note_content", content=None, title=note_title_in_special_folder_C3, folder=special_folder_name_C3)
                print(f"Get Content Response (C.3.3): {get_response_C3_verify}", file=sys.stderr)
                if isinstance(get_response_C3_verify, dict) and get_response_C3_verify.get("status") == "success":
                    retrieved_content_C3 = get_response_C3_verify.get('data', {}).get('content', '')
                    if note_content_C3 in retrieved_content_C3: print(f"SUCCESS (C.3.3 Get Verify): Core content found for note in special folder.", file=sys.stderr)
                    else: print(f"WARNING (C.3.3 Get Verify): Retrieved content mismatch for note in special folder. Expected '{note_content_C3}', Got '{retrieved_content_C3[:200]}...'", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        print("\n\n--- Section C.4: Tests for Content Size Boundaries ---", file=sys.stderr) # Corrected print statement
        empty_title_pt_C4_1 = "Empty Content Test Note S5.3.1 PT"
        print(f"\n--- Test C.4.1.1: Create '{empty_title_pt_C4_1}' with empty plain text content ---", file=sys.stderr)
        create_response_C4_1_pt = handle_request(action="create_note", title=empty_title_pt_C4_1, content="", folder=focused_test_folder, input_format="text")
        print(f"Create Response (C.4.1.1 PT): {create_response_C4_1_pt}", file=sys.stderr)
        if isinstance(create_response_C4_1_pt, dict) and create_response_C4_1_pt.get("status") == "success":
            get_response_C4_1_pt = handle_request(action="get_note_content", content=None, title=empty_title_pt_C4_1, folder=focused_test_folder)
            retrieved_C4_1_pt = get_response_C4_1_pt.get('data', {}).get('content', 'DefaultIfNotRetrieved')
            if retrieved_C4_1_pt is not None and len(retrieved_C4_1_pt) < 50 : print(f"SUCCESS (C.4.1.1 PT Get Verify): Retrieved content small/empty: '{retrieved_C4_1_pt[:50]}'", file=sys.stderr)
            else: print(f"WARNING (C.4.1.1 PT Get Verify): Retrieved content not empty/small: '{retrieved_C4_1_pt[:200]}...'", file=sys.stderr)
        
        empty_title_md_C4_1 = "Empty Content Test Note S5.3.1 MD"
        print(f"\n--- Test C.4.1.2: Create '{empty_title_md_C4_1}' with empty Markdown content ---", file=sys.stderr)
        create_response_C4_1_md = handle_request(action="create_note", title=empty_title_md_C4_1, content="", folder=focused_test_folder, input_format="markdown")
        print(f"Create Response (C.4.1.2 MD): {create_response_C4_1_md}", file=sys.stderr)
        if isinstance(create_response_C4_1_md, dict) and create_response_C4_1_md.get("status") == "success":
            get_response_C4_1_md = handle_request(action="get_note_content", content=None, title=empty_title_md_C4_1, folder=focused_test_folder)
            retrieved_C4_1_md = get_response_C4_1_md.get('data', {}).get('content', 'DefaultIfNotRetrieved')
            if retrieved_C4_1_md is not None and len(retrieved_C4_1_md) < 50 : print(f"SUCCESS (C.4.1.2 MD Get Verify): Retrieved content small/empty: '{retrieved_C4_1_md[:50]}'", file=sys.stderr)
            else: print(f"WARNING (C.4.1.2 MD Get Verify): Retrieved content not empty/small: '{retrieved_C4_1_md[:200]}...'", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        large_plain_text_block = "This is a moderately long line of plain text for testing purposes. "
        large_plain_text_content = "START_PLAIN_LARGE_S532_" + (large_plain_text_block * 800) + "_END_PLAIN_LARGE_S532"
        large_md_text_block = "### Large MD Section\\nThis is a paragraph within the large markdown content. It includes **bold** and *italic* text, and a `code snippet`.\\n\\n"
        large_markdown_content = "START_MD_LARGE_S533_\\n" + (large_md_text_block * 400) + "_END_MD_LARGE_S533"

        large_pt_title_C4_2 = "Large Content Plain Text Test Note S5.3.2"
        print(f"\n--- Test C.4.2: Create '{large_pt_title_C4_2}' with large plain text ({len(large_plain_text_content)} chars) ---", file=sys.stderr)
        create_response_C4_2 = handle_request(action="create_note", title=large_pt_title_C4_2, content=large_plain_text_content, folder=focused_test_folder, input_format="text")
        print(f"Create Response (C.4.2): {create_response_C4_2}", file=sys.stderr)
        if isinstance(create_response_C4_2, dict) and create_response_C4_2.get("status") == "success":
            get_response_C4_2 = handle_request(action="get_note_content", content=None, title=large_pt_title_C4_2, folder=focused_test_folder)
            retrieved_C4_2 = get_response_C4_2.get('data', {}).get('content', '')
            if "START_PLAIN_LARGE_S532_" in retrieved_C4_2 and "_END_PLAIN_LARGE_S532" in retrieved_C4_2 and large_plain_text_block in retrieved_C4_2: print(f"SUCCESS (C.4.2 Get Verify): Large plain text markers found. Length: {len(retrieved_C4_2)}", file=sys.stderr)
            else: print(f"WARNING (C.4.2 Get Verify): Large plain text markers not found. Retrieved len: {len(retrieved_C4_2)}.", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        large_md_title_C4_3 = "Large Content Markdown Test Note S5.3.3"
        print(f"\n--- Test C.4.3: Create '{large_md_title_C4_3}' with large Markdown ({len(large_markdown_content)} chars source) ---", file=sys.stderr)
        create_response_C4_3 = handle_request(action="create_note", title=large_md_title_C4_3, content=large_markdown_content, folder=focused_test_folder, input_format="markdown")
        print(f"Create Response (C.4.3): {create_response_C4_3}", file=sys.stderr)
        if isinstance(create_response_C4_3, dict) and create_response_C4_3.get("status") == "success":
            get_response_C4_3 = handle_request(action="get_note_content", content=None, title=large_md_title_C4_3, folder=focused_test_folder)
            retrieved_C4_3 = get_response_C4_3.get('data', {}).get('content', '')
            if "START_MD_LARGE_S533" in retrieved_C4_3 and "_END_MD_LARGE_S533" in retrieved_C4_3 and "Large MD Section" in retrieved_C4_3 and "<code>code snippet</code>" in retrieved_C4_3: print(f"SUCCESS (C.4.3 Get Verify): Large MD markers found. Length: {len(retrieved_C4_3)}", file=sys.stderr)
            else: print(f"WARNING (C.4.3 Get Verify): Large MD markers not found. Retrieved len: {len(retrieved_C4_3)}.", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        empty_append_target_title_C4_4 = "Target for Empty Append S5.3.4"
        initial_content_C4_4 = "Initial content for empty append test."
        print(f"\n--- Test C.4.4 Setup: Create '{empty_append_target_title_C4_4}' ---", file=sys.stderr)
        handle_request(action="create_note", title=empty_append_target_title_C4_4, content=initial_content_C4_4, folder=focused_test_folder, input_format="text")
        print(f"\n--- Test C.4.4.1: Append empty plain text to '{empty_append_target_title_C4_4}' ---", file=sys.stderr)
        handle_request(action="append_note", title=empty_append_target_title_C4_4, content="", folder=focused_test_folder, input_format="text")
        print(f"\n--- Test C.4.4.2: Append empty Markdown to '{empty_append_target_title_C4_4}' ---", file=sys.stderr)
        handle_request(action="append_note", title=empty_append_target_title_C4_4, content="", folder=focused_test_folder, input_format="markdown")
        get_response_C4_4_verify = handle_request(action="get_note_content", content=None, title=empty_append_target_title_C4_4, folder=focused_test_folder)
        retrieved_C4_4 = get_response_C4_4_verify.get('data', {}).get('content', '')
        if initial_content_C4_4 in retrieved_C4_4 and len(retrieved_C4_4) < (len(initial_content_C4_4) + 100): print(f"SUCCESS (C.4.4 Verify): Content after empty appends reasonable.", file=sys.stderr)
        else: print(f"WARNING (C.4.4 Verify): Content after empty appends not as expected. Retrieved: '{retrieved_C4_4[:200]}...'", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        large_append_pt_title_C4_5 = "Target for Large Append Plain Text S5.3.5"
        initial_content_C4_5 = "INITIAL_CONTENT_FOR_LARGE_APPEND_PT_S535. "
        print(f"\n--- Test C.4.5 Setup: Create '{large_append_pt_title_C4_5}' ---", file=sys.stderr)
        handle_request(action="create_note", title=large_append_pt_title_C4_5, content=initial_content_C4_5, folder=focused_test_folder, input_format="text")
        print(f"\n--- Test C.4.5: Append large plain text to '{large_append_pt_title_C4_5}' ---", file=sys.stderr)
        append_response_C4_5 = handle_request(action="append_note", title=large_append_pt_title_C4_5, content=large_plain_text_content, folder=focused_test_folder, input_format="text")
        print(f"Append Response (C.4.5): {append_response_C4_5}", file=sys.stderr)
        if isinstance(append_response_C4_5, dict) and append_response_C4_5.get("status") == "success":
            get_response_C4_5 = handle_request(action="get_note_content", content=None, title=large_append_pt_title_C4_5, folder=focused_test_folder)
            retrieved_C4_5 = get_response_C4_5.get('data', {}).get('content', '')
            if initial_content_C4_5 in retrieved_C4_5 and "START_PLAIN_LARGE_S532_" in retrieved_C4_5 and "_END_PLAIN_LARGE_S532" in retrieved_C4_5: print(f"SUCCESS (C.4.5 Get Verify): Large plain text append markers found. Length: {len(retrieved_C4_5)}", file=sys.stderr)
            else: print(f"WARNING (C.4.5 Get Verify): Large plain text append markers not found. Len: {len(retrieved_C4_5)}.", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        large_append_md_title_C4_6 = "Target for Large Append Markdown S5.3.6"
        initial_content_C4_6 = "INITIAL_CONTENT_FOR_LARGE_APPEND_MD_S536. "
        print(f"\n--- Test C.4.6 Setup: Create '{large_append_md_title_C4_6}' ---", file=sys.stderr)
        handle_request(action="create_note", title=large_append_md_title_C4_6, content=initial_content_C4_6, folder=focused_test_folder, input_format="text")
        print(f"\n--- Test C.4.6: Append large Markdown to '{large_append_md_title_C4_6}' ---", file=sys.stderr)
        append_response_C4_6 = handle_request(action="append_note", title=large_append_md_title_C4_6, content=large_markdown_content, folder=focused_test_folder, input_format="markdown")
        print(f"Append Response (C.4.6): {append_response_C4_6}", file=sys.stderr)
        if isinstance(append_response_C4_6, dict) and append_response_C4_6.get("status") == "success":
            get_response_C4_6 = handle_request(action="get_note_content", content=None, title=large_append_md_title_C4_6, folder=focused_test_folder)
            retrieved_C4_6 = get_response_C4_6.get('data', {}).get('content', '')
            if initial_content_C4_6 in retrieved_C4_6 and "START_MD_LARGE_S533" in retrieved_C4_6 and "_END_MD_LARGE_S533" in retrieved_C4_6 and "<code>code snippet</code>" in retrieved_C4_6 : print(f"SUCCESS (C.4.6 Get Verify): Large MD append markers found. Length: {len(retrieved_C4_6)}", file=sys.stderr)
            else: print(f"WARNING (C.4.6 Get Verify): Large MD append markers not found. Len: {len(retrieved_C4_6)}.", file=sys.stderr)
        print("---------------------------------", file=sys.stderr)

        print("\n--- Full Test Suite Run Complete ---", file=sys.stderr)
    else:
        # MCP Server Mode
        raw_input_for_error_reporting = "" 
        try:
            input_data_from_stdin = sys.stdin.read() 
            raw_input_for_error_reporting = input_data_from_stdin

            if not raw_input_for_error_reporting.strip(): 
                error_response = {"status": "error", "message": "No input received on stdin or input was empty."}
                print(f"ERROR: No input received on stdin or input was empty.", file=sys.stderr)
                print(json.dumps(error_response), file=sys.stdout)
                sys.exit(1)
                
            print(f"DEBUG: Received raw input on stdin: {raw_input_for_error_reporting}", file=sys.stderr)

            input_data = json.loads(raw_input_for_error_reporting)
            print(f"DEBUG: Parsed input data: {input_data}", file=sys.stderr)

            action = input_data.get("action")
            content = input_data.get("content")
            title = input_data.get("title")
            folder = input_data.get("folder")
            input_format = input_data.get("input_format", "text")

            if action is None or content is None: 
                 error_response = {"status": "error", "message": "Missing 'action' or 'content' in request."}
                 print(f"ERROR: Missing 'action' or 'content'. Raw input: '{raw_input_for_error_reporting.strip()}'", file=sys.stderr)
                 print(json.dumps(error_response), file=sys.stdout)
                 sys.exit(1)

            response = handle_request(action=action, content=content, title=title, folder=folder, input_format=input_format)
            print(json.dumps(response), file=sys.stdout)

        except json.JSONDecodeError as e:
            error_response = {"status": "error", "message": "Invalid JSON input."}
            print(f"ERROR: Invalid JSON received. Raw input: '{raw_input_for_error_reporting.strip()}'. Exception: {str(e)}", file=sys.stderr)
            print(json.dumps(error_response), file=sys.stdout)
            sys.exit(1)
        except TypeError as e: 
            error_response = {"status": "error", "message": f"Service call error: {str(e)}"}
            print(f"ERROR: TypeError during MCP processing. Input: '{raw_input_for_error_reporting.strip()}'. Exception: {str(e)}", file=sys.stderr)
            print(json.dumps(error_response), file=sys.stdout)
            sys.exit(1)
        except Exception as e: 
            error_response = {"status": "error", "message": "An unexpected server-side error occurred."}
            print(f"ERROR: Unexpected exception during MCP processing. Input: '{raw_input_for_error_reporting.strip()}'. Exception: {type(e).__name__} - {str(e)}", file=sys.stderr)
            print(json.dumps(error_response), file=sys.stdout)
            sys.exit(1)
'''