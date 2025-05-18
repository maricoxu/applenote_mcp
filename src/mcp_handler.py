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
                # Use a consistent set of extensions, including nl2br for better multiline handling in Notes
                processed_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br'])
                print(f"INFO: Content converted from Markdown to HTML (with nl2br): '{processed_content[:100]}...'" if processed_content else "INFO: Content converted from Markdown to HTML: [EMPTY]")
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

    elif action == "list_notes":
        script_name_to_use = "list_notes.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)
        if not os.path.exists(applescript_path):
            return f"Error: Script {script_name_to_use} not found."
        
        effective_folder = folder if folder else ""
        try:
            cmd = ["osascript", applescript_path, effective_folder]
            print(f"INFO: Executing AppleScript: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            raw_output = result.stdout.strip()
            print(f"SUCCESS: AppleScript executed for list_notes. Raw Output: {raw_output[:200]}...")
            if raw_output.startswith("错误：") or raw_output.startswith("信息："):
                 # Script returns specific info/error messages as direct strings
                return f"Result from list_notes: {raw_output}"
            
            # Split the string of titles by newline into a list
            titles_list = raw_output.splitlines()
            return {"status": "success", "titles": titles_list, "message": f"Successfully listed notes from folder '{effective_folder if effective_folder else 'All Notes'}'."}
        except subprocess.CalledProcessError as e:
            raw_stdout = e.stdout.strip()
            if raw_stdout.startswith("错误：") or raw_stdout.startswith("信息："):
                return f"Result from list_notes: {raw_stdout}"
            else:
                return f"Error executing '{script_name_to_use}': {e.stderr.strip() if e.stderr else raw_stdout}"
        except FileNotFoundError:
            return f"Error: {script_name_to_use} command not found."

    elif action == "get_note_content":
        if not title:
            return "Error: Title parameter is required for get_note_content action."
        
        script_name_to_use = "get_note_content.scpt"
        applescript_path = os.path.join(BASE_APPLESCRIPT_PATH, script_name_to_use)
        if not os.path.exists(applescript_path):
            return f"Error: Script {script_name_to_use} not found."

        effective_folder = folder if folder else ""
        try:
            cmd = ["osascript", applescript_path, title, effective_folder]
            print(f"INFO: Executing AppleScript: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            note_content = result.stdout.strip() # AppleScript directly returns body or error string
            print(f"SUCCESS: AppleScript executed for get_note_content. Output: {note_content[:200]}...")

            if note_content.startswith("错误："):
                return f"Error getting content for note '{title}': {note_content}"
            
            return {"status": "success", "title": title, "content": note_content, "folder": effective_folder}
        except subprocess.CalledProcessError as e:
            raw_stdout = e.stdout.strip()
            if raw_stdout.startswith("错误："):
                return f"Error getting content for note '{title}': {raw_stdout}"
            else:
                return f"Error executing '{script_name_to_use}': {e.stderr.strip() if e.stderr else raw_stdout}"
        except FileNotFoundError:
            return f"Error: {script_name_to_use} command not found."

    else:
        print(f"WARN: Action '{action}' is not recognized.")
        return f"Error: Action '{action}' not recognized."

if __name__ == "__main__":
    # --- Capture initial markdown module state at the very beginning of the test suite ---
    # This helps in restoring it consistently after tests that might alter it.
    # The `markdown` variable is defined at the module level based on initial import success.
    initial_global_markdown_module_state = None
    if 'markdown' in globals() and globals()['markdown'] is not None:
        initial_global_markdown_module_state = markdown
    elif markdown is None: # Explicitly check if it was already None from the start
        pass # initial_global_markdown_module_state remains None
    else: # Should not happen if markdown is defined one way or another
        print("WARN: Initial global markdown module state is indeterminate!")

    # --- Helper function to call delete script (remains the same) ---
    def cleanup_note(title_to_delete, folder_name):
        print(f"--- Attempting to delete note \\'{title_to_delete}\\' from folder \\'{folder_name}\\' ---")
        script_path = os.path.join(BASE_APPLESCRIPT_PATH, "delete_note_by_title.scpt")
        if not os.path.exists(script_path):
            print(f"WARN: Cleanup script \\'delete_note_by_title.scpt\\' not found at {script_path}")
            return "Error: delete_note_by_title.scpt not found."
        try:
            cmd = ["osascript", script_path, title_to_delete, folder_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False) # check=False for cleanup
            output = result.stdout.strip() if result.stdout else ""
            if result.stderr.strip():
                output += " STDERR: " + result.stderr.strip()
            print(f"Cleanup result for \\'{title_to_delete}\\' (in {folder_name if folder_name else 'default'}): {output}")
            return output
        except Exception as e:
            print(f"Exception during cleanup of \\'{title_to_delete}\\': {e}")
            return f"Exception during cleanup: {e}"

    print("--- Full Test Suite for MCP Handler ---")

    # --- Test Variables for Focused/Initial Part ---
    focused_test_folder = "MCP Tests"
    focused_target_title = "Append Test Target S3" # This is a key note used in many tests
    focused_initial_content = "Initial content for focused append test."
    focused_append_text = " This is focused appended plain text."
    focused_append_md = "## Appended Section\\n* Item A\\n* Item B"
    # Name of a potentially mistitled note from past bugs, good to cleanup
    mistitled_cleanup_target = "Initial content for append test." 

    # --- Global Cleanup for notes that will be created by this full suite ---
    print("\\n--- Global Initial Cleanup Phase ---")
    cleanup_note(focused_target_title, focused_test_folder)
    cleanup_note(mistitled_cleanup_target, focused_test_folder) 
    cleanup_note("Markdown Test Note S2", focused_test_folder)
    cleanup_note("Plain Text Default S2", "") # Default folder
    cleanup_note("MD Fallback Test S2", focused_test_folder)
    # Note: Test 4 (empty title) is harder to clean selectively by title. We'll let it run.
    # Test 9 (Duplicate Name Note) is manual, so no cleanup here.

    # --- Focused Test Block (Steps 1-8 from previous focused run, now integrated) ---
    print("\\n--- Section A: Focused Create, List, Get, Append Tests (formerly Stage 4 focused test) ---")
    
    # A.1. Create Note (this is 'Append Test Target S3')
    print(f"\\n--- A.1. Create \\'{focused_target_title}\\' ---")
    # Cleanup already done globally, so we expect this to be a fresh creation.
    create_response_A1 = handle_request(action="create_note", content=focused_initial_content, title=focused_target_title, folder=focused_test_folder, input_format="text")
    print(f"Create Response (A.1): {create_response_A1}")

    # A.2. List Notes to Verify
    print(f"\\n--- A.2. List notes in \\'{focused_test_folder}\\' after A.1 creation ---")
    list_response_A2 = handle_request(action="list_notes", content=None, folder=focused_test_folder)
    print(f"List Response (A.2): {list_response_A2}")
    if isinstance(list_response_A2, dict) and list_response_A2.get("status") == "success":
        titles_A2 = list_response_A2.get('titles', [])
        print(f"Notes found (A.2): {titles_A2}")
        count_A2 = titles_A2.count(focused_target_title)
        print(f"Occurrences of \\'{focused_target_title}\\' (A.2): {count_A2}")
        if count_A2 != 1:
            print(f"WARNING (A.2): Expected 1 occurrence of \\'{focused_target_title}\\' but found {count_A2}.")
        if focused_initial_content in titles_A2: # Check for mistitled note by content
             print(f"WARNING (A.2): A note titled with initial content \\'{focused_initial_content}\\' was also found!")

    # A.3. Get Content of the Created Note
    print(f"\\n--- A.3. Get content of \\'{focused_target_title}\\' ---")
    get_response_A3 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
    print(f"Get Content Response (A.3): {get_response_A3}")
    if isinstance(get_response_A3, dict) and get_response_A3.get("status") == "success":
        print(f"Retrieved content (A.3): {get_response_A3.get('content')}")

    # A.4. Append Text Content
    print(f"\\n--- A.4. Append text to \\'{focused_target_title}\\' ---")
    append_text_response_A4 = handle_request(action="append_note", content=focused_append_text, title=focused_target_title, folder=focused_test_folder, input_format="text")
    print(f"Append Text Response (A.4): {append_text_response_A4}")

    # A.5. Get Content After Text Append
    print(f"\\n--- A.5. Get content of \\'{focused_target_title}\\' after text append ---")
    get_response_A5 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
    print(f"Get Content Response (A.5): {get_response_A5}")
    if isinstance(get_response_A5, dict) and get_response_A5.get("status") == "success":
        retrieved_content_A5 = get_response_A5.get('content','')
        print(f"Retrieved content (A.5): {retrieved_content_A5}")
        if focused_initial_content in retrieved_content_A5 and focused_append_text.strip() in retrieved_content_A5:
            print("Content after text append (A.5) seems correct.")
        else:
            print("WARNING (A.5): Content after text append might be incorrect.")

    # A.6. Append Markdown Content
    print(f"\\n--- A.6. Append Markdown to \\'{focused_target_title}\\' ---")
    # This test expects markdown to be available. We ensure it is, possibly re-importing if B.3 left it as None.
    if 'markdown' not in globals() or markdown is None:
        print("INFO (A.6): markdown module was None or not in globals, attempting to ensure it is available.")
        if initial_global_markdown_module_state is not None:
            markdown = initial_global_markdown_module_state
            print("INFO (A.6): Restored markdown from initial global state.")
        else:
            try:
                import markdown as md_lib_A6 # Try fresh import
                markdown = md_lib_A6
                print("INFO (A.6): Markdown library dynamically imported for test A.6.")
            except ImportError:
                print("WARN (A.6): Markdown library not installed, cannot test MD append properly.")
                markdown = None # Still None if import fails
    
    append_md_response_A6 = handle_request(action="append_note", content=focused_append_md, title=focused_target_title, folder=focused_test_folder, input_format="markdown")
    print(f"Append MD Response (A.6): {append_md_response_A6}")
    # No specific restoration here, subsequent tests will re-evaluate or use initial_global_markdown_module_state

    # A.7. Get Content After Markdown Append
    print(f"\\n--- A.7. Get content of \\'{focused_target_title}\\' after MD append ---")
    get_response_A7 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
    print(f"Get Content Response (A.7): {get_response_A7}")
    if isinstance(get_response_A7, dict) and get_response_A7.get("status") == "success":
        retrieved_content_A7 = get_response_A7.get('content', '')
        print(f"Retrieved content (A.7): {retrieved_content_A7}")
        all_present_A7 = True
        if focused_initial_content not in retrieved_content_A7: all_present_A7 = False
        if "Appended Section" not in retrieved_content_A7: all_present_A7 = False
        if "Item A" not in retrieved_content_A7: all_present_A7 = False
        if "Item B" not in retrieved_content_A7: all_present_A7 = False
        if all_present_A7:
             print("Content after MD append (A.7) seems correct.")
        else:
            print("WARNING (A.7): Content after MD append might be incorrect.")

    # --- Section B: Original Test Suite (adapted with cleanup) ---
    print("\\n\\n--- Section B: Adapted Original Test Suite ---")
    
    # Test B.1 (Original Test 1, part 1 - Markdown Test Note S2)
    # focused_target_title ('Append Test Target S3') was created in Section A
    # So we only need to create "Markdown Test Note S2" here if it's used independently.
    # Cleanup for "Markdown Test Note S2" was done globally.
    print("\\n--- Test B.1 (Create): Create 'Markdown Test Note S2' ---")
    md_content_B1 = "# My Markdown Note\\n\\nThis is a *test* with [a link](http://example.com) and some `code`.\\n\\n- Item 1\\n- Item 2"
    handle_request(action="create_note", content=md_content_B1, title="Markdown Test Note S2", folder=focused_test_folder, input_format="markdown")
    print("---------------------------------")

    # Test B.2 (Original Test 2 - Plain Text Default S2)
    # Cleanup for "Plain Text Default S2" was done globally.
    print("\\n--- Test B.2 (Create): Create 'Plain Text Default S2' in default folder ---")
    text_content_B2 = "This is a plain text note for the default folder."
    handle_request(action="create_note", content=text_content_B2, title="Plain Text Default S2", folder="", input_format="text")

    # Test B.3 (Original Test 3 - MD Fallback Test S2)
    # Cleanup for "MD Fallback Test S2" was done globally.
    print("\\n--- Test B.3 (Create): Create 'MD Fallback Test S2' (simulating missing markdown lib) ---")
    
    # Store the initial state of the markdown module reference
    initial_markdown_module = None
    if 'markdown' in globals() and globals()['markdown'] is not None:
        initial_markdown_module = markdown
    
    # Simulate missing library
    markdown = None 
    print(f"DEBUG: markdown module set to None for Test B.3")

    handle_request(action="create_note", content="# Test MD Fallback\\nThis should be plain.", title="MD Fallback Test S2", folder=focused_test_folder, input_format="markdown")
    
    # Restore the markdown module
    if initial_markdown_module is not None:
        markdown = initial_markdown_module
        print(f"DEBUG: markdown module restored to its initial state for Test B.3")
    else:
        # If it was None initially or couldn't be captured, try to re-import to be safe for subsequent tests
        try:
            import markdown as md_restored
            markdown = md_restored
            print(f"DEBUG: markdown module re-imported for Test B.3")
        except ImportError:
            markdown = None # Still None if re-import fails
            print(f"DEBUG: markdown module remains None after failed re-import for Test B.3")
    
    # Test B.4 (Original Test 4 - Empty title note)
    # No specific pre-cleanup by title.
    print("\\n--- Test B.4 (Create): Create note with an empty title ---")
    # It's good practice to clean up notes with empty titles if possible, perhaps by content or a known temporary ID if a more robust cleanup is needed.
    # For now, we will clean up any note with title "" in "MCP Tests" folder. This might affect other tests if they also create notes with "" title.
    cleanup_note("", focused_test_folder) # Attempt to clean any previous empty title note in this folder.
    handle_request(action="create_note", content="Content for note with empty title for stage 2.", title="", folder=focused_test_folder, input_format="text")
    print("---------------------------------")

    # Test B.5 (Original Test 5 - Append plain text to 'Append Test Target S3')
    # 'Append Test Target S3' should exist from Section A and have content.
    print("\\n--- Test B.5 (Append): Append plain text to 'Append Test Target S3' (again) ---")
    handle_request(action="append_note", content=" This is a second plain text append (Test B.5).", title=focused_target_title, folder=focused_test_folder, input_format="text")

    # Test B.6 (Original Test 6 - Append Markdown to 'Append Test Target S3')
    print(f"\\n--- Test B.6 (Append): Append Markdown to \\'{focused_target_title}\\' (again) ---")
    appended_md_content_B6 = "### Another MD Section\\n1. One\\n2. Two"
    # This test expects markdown to be available.
    if 'markdown' not in globals() or markdown is None:
        print("INFO (B.6): markdown module was None or not in globals, attempting to ensure it is available.")
        if initial_global_markdown_module_state is not None:
            markdown = initial_global_markdown_module_state
            print("INFO (B.6): Restored markdown from initial global state.")
        else:
            try: 
                import markdown as md_lib_B6 # Try fresh import
                markdown = md_lib_B6
                print("INFO (B.6): MD lib dynamically imported for B.6.")
            except ImportError: 
                print("WARN (B.6): MD lib not found for B.6.")
                markdown = None # Still None
    
    handle_request(action="append_note", content=appended_md_content_B6, title=focused_target_title, folder=focused_test_folder, input_format="markdown")
    # No specific restoration here, rely on next test or global state if needed.

    # Test B.7 (Original Test 7 - Append to non-existent note)
    print("\\n--- Test B.7 (Append): Attempt to append to a non-existent note ---")
    cleanup_note("NonExistent Note For Append B7", focused_test_folder) # Ensure it's non-existent
    handle_request(action="append_note", content="This should fail.", title="NonExistent Note For Append B7", folder=focused_test_folder, input_format="text")

    # Test B.8 (Original Test 8 - Append with empty title)
    print("\\n--- Test B.8 (Append): Attempt to append with an empty title ---")
    handle_request(action="append_note", content="This should fail due to no title.", title="", folder=focused_test_folder, input_format="text")

    # Test B.9 (Original Test 9 - Placeholder for append to multiple notes)
    print("\\n--- Test B.9 (Append): Placeholder for testing append to multiple notes (manual setup) ---")
    print("(Skipping Test B.9 - requires manual creation of duplicate notes in 'MCP Tests' folder named 'Duplicate Name Note')")

    # Test B.10 (Original Test 10 - List notes from 'MCP Tests')
    print("\\n--- Test B.10 (List): List notes from 'MCP Tests' folder (end of suite) ---")
    list_result_B10 = handle_request(action="list_notes", content=None, folder=focused_test_folder)
    print(f"List MCP Tests Result (B.10): {list_result_B10}")

    # Test B.11 (Original Test 11 - List notes from all notes)
    print("\\n--- Test B.11 (List): List notes from all notes (default folder, end of suite) ---")
    list_result_B11 = handle_request(action="list_notes", content=None, folder="") 
    print(f"List All Notes Result (B.11): {list_result_B11}")

    # Test B.12 (Original Test 12 - Get content of 'Append Test Target S3')
    print("\\n--- Test B.12 (Get Content): Get final content of 'Append Test Target S3' ---")
    get_content_result_B12 = handle_request(action="get_note_content", content=None, title=focused_target_title, folder=focused_test_folder)
    print(f"Get Final Content Result for \\'{focused_target_title}\\' (B.12): {get_content_result_B12}")
    if isinstance(get_content_result_B12, dict) and get_content_result_B12.get("status") == "success":
        final_content_B12 = get_content_result_B12.get('content', '')
        print(f"Retrieved final content (B.12): {final_content_B12}")
        # Check for key parts from all appends
        if focused_initial_content in final_content_B12 and \
           focused_append_text.strip() in final_content_B12 and \
           "Appended Section" in final_content_B12 and "Item A" in final_content_B12 and \
           "This is a second plain text append (Test B.5)." in final_content_B12 and \
           "Another MD Section" in final_content_B12 and "One" in final_content_B12:
            print("Final content of 'Append Test Target S3' (B.12) seems correct with all appends.")
        else:
            print("WARNING (B.12): Final content of 'Append Test Target S3' might be missing some parts.")


    # Test B.13 (Original Test 13 - Get content of a non-existent note)
    print("\\n--- Test B.13 (Get Content): Attempt to get content of a non-existent note ---")
    cleanup_note("NonExistent Note For GetContent B13", focused_test_folder) # Ensure non-existent
    get_content_non_existent_B13 = handle_request(action="get_note_content", content=None, title="NonExistent Note For GetContent B13", folder=focused_test_folder)
    print(f"Get Content Non-Existent Result (B.13): {get_content_non_existent_B13}")

    # Test B.14 (Original Test 14 - List notes from a non-existent folder)
    print("\\n--- Test B.14 (List): List notes from a non-existent folder ---")
    list_non_existent_folder_B14 = handle_request(action="list_notes", content=None, folder="FolderThatDoesNotExist_B14")
    print(f"List Non-Existent Folder Result (B.14): {list_non_existent_folder_B14}")

    print("\\n--- Full Test Suite Run Complete ---")
