import subprocess
import os

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
    print("--- MCP Request Received ---")
    print(f"Action: {action}")
    print(f"Input Format: {input_format}")
    # For append_note, content is what to append. For create_note, it's the initial body.
    # Title and folder are relevant for both, specifying the target note.
    if action == "append_note":
        print(f"Content to Append: '{content[:100]}...'" if content else "Content to Append: [EMPTY]")
    else: # create_note or others
        print(f"Raw Content: '{content[:100]}...'" if content else "Raw Content: [EMPTY]")
    
    if title:
        print(f"Title: '{title}'")
    if folder:
        print(f"Folder: '{folder}'")
    print("--- End of MCP Request ---")

    processed_content = content
    if input_format == "markdown" and action in ["create_note", "append_note"]:
        if markdown:
            try:
                # For append, if we want HTML, newlines in MD should become <br> or be part of <p>
                # The python-markdown library by default wraps output in <p> if no other block element is found at the root.
                # If appending multiple MD blocks, each might become its own <p> or list, etc.
                processed_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
                print(f"INFO: Content converted from Markdown to HTML: '{processed_content[:100]}...'" if processed_content else "INFO: Content converted from Markdown to HTML: [EMPTY]")
            except Exception as e:
                print(f"WARN: Markdown to HTML conversion failed: {e}. Using raw content.")
        else:
            print("WARN: `markdown` library not installed. Cannot convert Markdown to HTML. Using raw content.")

    if action == "create_note":
        script_name_to_use = "create_note_advanced.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)

        if not os.path.exists(applescript_path):
            print(f"WARN: AppleScript file not found at {applescript_path}. Cannot execute.")
            return f"Error: Script {script_name_to_use} not found."
        else:
            try:
                effective_title = title if title else ""
                effective_folder = folder if folder else ""
                
                # Parameters for create_note_advanced.scpt: body, title, folder
                # CORRECTED based on AppleScript: noteTitle, noteBody, targetFolder
                cmd = ["osascript", applescript_path, effective_title, processed_content, effective_folder]
                print(f"INFO: Executing AppleScript: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                print(f"SUCCESS: AppleScript executed. Output: {result.stdout.strip()}")
                display_title = title if title else "Untitled"
                return f"Success: Note '{display_title}' processed (created). Details: {result.stdout.strip()}"
            except subprocess.CalledProcessError as e:
                print(f"ERROR: AppleScript execution failed for '{script_name_to_use}'.")
                print(f"  Return code: {e.returncode}")
                print(f"  Stdout: {e.stdout.strip()}")
                print(f"  Stderr: {e.stderr.strip()}")
                return f"Error executing '{script_name_to_use}': {e.stderr.strip() if e.stderr else e.stdout.strip()}"
            except FileNotFoundError:
                print(f"ERROR: osascript command not found. Please ensure it is in your PATH.")
                return "Error: osascript command not found."

    elif action == "append_note":
        if not title: # Title is mandatory for append
            print("ERROR: Title parameter is required for append_note action.")
            return "Error: Title parameter is required for append_note action."
        
        # Content can be empty if the user just wants to append a newline essentially (though script handles linefeed)
        # For this action, processed_content is the content_to_append
        content_to_append = processed_content if processed_content is not None else "" # Ensure it's a string

        script_name_to_use = "append_to_note.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)

        if not os.path.exists(applescript_path):
            print(f"WARN: AppleScript file not found at {applescript_path}. Cannot execute.")
            return f"Error: Script {script_name_to_use} not found."
        else:
            try:
                effective_folder = folder if folder else ""
                
                # Parameters for append_to_note.scpt: targetTitle, targetFolder, contentToAppend
                cmd = ["osascript", applescript_path, title, effective_folder, content_to_append]
                print(f"INFO: Executing AppleScript: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                print(f"SUCCESS: AppleScript executed. Output: {result.stdout.strip()}")
                return f"Success: Note '{title}' processed (appended). Details: {result.stdout.strip()}"
            except subprocess.CalledProcessError as e:
                # AppleScript for append_note is designed to return specific error messages in stdout for common issues
                # (e.g., note not found, multiple notes found), and these don't always mean a non-zero exit code
                # if the script itself handles it gracefully by returning a string starting with "错误：".
                # However, subprocess.run with check=True will raise for non-zero exit if osascript itself fails hard.
                # We check stdout for our specific error prefixes from the AppleScript.
                raw_stdout = e.stdout.strip()
                if raw_stdout.startswith("错误："):
                    print(f"INFO: AppleScript reported an issue for '{script_name_to_use}': {raw_stdout}")
                    return f"Error processing append for note '{title}': {raw_stdout}" 
                else:
                    print(f"ERROR: AppleScript execution failed for '{script_name_to_use}'.")
                    print(f"  Return code: {e.returncode}")
                    print(f"  Stdout: {raw_stdout}")
                    print(f"  Stderr: {e.stderr.strip()}")
                    return f"Error executing '{script_name_to_use}': {e.stderr.strip() if e.stderr else raw_stdout}"
            except FileNotFoundError:
                print(f"ERROR: osascript command not found. Please ensure it is in your PATH.")
                return "Error: osascript command not found."
    else:
        print(f"WARN: Action '{action}' is not recognized.")
        return f"Error: Action '{action}' not recognized."

if __name__ == "__main__":
    print("Testing MCP Handler - Stage 2 & 3 Features")
    print("\n--- Test 1 (Create): Create note with Markdown content in a specific folder ---")
    md_content = "# My Markdown Note\n\nThis is a *test* with [a link](http://example.com) and some `code`.\n\n- Item 1\n- Item 2"
    # Ensure this note exists for append tests later. We'll target this one.
    target_note_title_for_append = "Append Test Target S3"
    target_note_initial_content = "Initial content for append test."
    handle_request(action="create_note", content=target_note_initial_content, title=target_note_title_for_append, folder="MCP Tests", input_format="text")
    print("---------------------------------")
    handle_request(action="create_note", content=md_content, title="Markdown Test Note S2", folder="MCP Tests", input_format="markdown")
    
    print("\n--- Test 2 (Create): Create note with plain text in default folder ---")
    text_content = "This is a plain text note for the default folder."
    handle_request(action="create_note", content=text_content, title="Plain Text Default S2", folder="", input_format="text")

    print("\n--- Test 3 (Create): Create note if markdown library is missing (simulated) ---")
    original_markdown_lib_state = markdown # Store original state
    markdown = None # Simulate missing library
    handle_request(action="create_note", content="# Test MD Fallback\nThis should be plain.", title="MD Fallback Test S2", folder="MCP Tests", input_format="markdown")
    markdown = original_markdown_lib_state # Restore it
    
    print("\n--- Test 4 (Create): Create note with an empty title (AppleScript should handle) ---")
    handle_request(action="create_note", content="Content for note with empty title for stage 2.", title="", folder="MCP Tests", input_format="text")
    print("---------------------------------")

    print("\n--- Test 5 (Append): Append plain text to an existing note ---")
    handle_request(action="append_note", content="This is appended plain text.", title=target_note_title_for_append, folder="MCP Tests", input_format="text")

    print("\n--- Test 6 (Append): Append Markdown (converted to HTML if lib available) to an existing note ---")
    appended_md_content = "\n*   Appended list item 1\n*   Appended list item 2"
    # Restore markdown lib if it was None for previous test, to test actual conversion for append
    if not markdown and original_markdown_lib_state:
        markdown = original_markdown_lib_state
    handle_request(action="append_note", content=appended_md_content, title=target_note_title_for_append, folder="MCP Tests", input_format="markdown")

    print("\n--- Test 7 (Append): Attempt to append to a non-existent note ---")
    handle_request(action="append_note", content="This should fail.", title="NonExistent Note For Append", folder="MCP Tests", input_format="text")

    print("\n--- Test 8 (Append): Attempt to append with an empty title ---")
    handle_request(action="append_note", content="This should fail due to no title.", title="", folder="MCP Tests", input_format="text")

    # To test 'multiple notes found', you'd need to manually create them in Notes first.
    print("\n--- Test 9 (Append): Placeholder for testing append to multiple notes with same name (manual setup needed) ---")
    # handle_request(action="append_note", content="Testing multiple.", title="Duplicate Name Note", folder="MCP Tests", input_format="text")
    print("(Skipping Test 9 - requires manual creation of duplicate notes in 'MCP Tests' folder named 'Duplicate Name Note')")
