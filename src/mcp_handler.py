'''
import subprocess
import json
import sys
import os # For path joining
import markdown # For Markdown conversion

# --- AppleScript Execution ---
def run_applescript(script_name, *args):
    # Construct the full path to the script
    script_path = os.path.join(os.path.dirname(__file__), 'applescripts', script_name)
    try:
        process = subprocess.run(['osascript', script_path] + list(args), capture_output=True, text=True, check=True)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_message = f"AppleScript Error: {e.stderr.strip()}"
        # print(f"stdout: {e.stdout}", file=sys.stderr) 
        # print(f"stderr: {e.stderr}", file=sys.stderr)
        # print(f"args: {args}", file=sys.stderr)
        # print(f"script_path: {script_path}", file=sys.stderr)
        raise ValueError(error_message) 
    except FileNotFoundError:
        error_message = f"AppleScript Error: Script not found at {script_path}"
        # print(error_message, file=sys.stderr)
        raise FileNotFoundError(error_message)

# --- Note Operations ---
def create_note(folder, title, content, plain_text=False):
    if not plain_text and content:
        # Convert Markdown to HTML, nl2br for line breaks, fenced_code for code blocks, tables for tables
        html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br'])
    else:
        html_content = content  # Use plain text directly or if content is None/empty

    if folder is None: # Ensure folder is not None for AppleScript
        folder = "" 
    
    script_name = 'create_note_advanced.scpt' if folder or title else 'create_note_basic.scpt'
    
    if script_name == 'create_note_advanced.scpt':
        return run_applescript(script_name, folder, title, html_content or "") # Ensure content is not None
    else: # basic script only takes content
        return run_applescript(script_name, html_content or "")


def append_note(folder, title, content_to_append):
    if not content_to_append: # Don't append if content is empty
        return "No content provided to append."
    html_content_to_append = markdown.markdown(content_to_append, extensions=['fenced_code', 'tables', 'nl2br'])
    return run_applescript('append_to_note.scpt', folder, title, html_content_to_append)

def list_notes(folder=None):
    if folder:
        return run_applescript('list_notes.scpt', folder)
    else:
        return run_applescript('list_notes.scpt') # Script handles optional folder

def get_note_content(folder, title):
    return run_applescript('get_note_content.scpt', folder, title)

def delete_note_by_title(folder, title): # Keep for testing or potential MCP action
    return run_applescript('delete_note_by_title.scpt', folder, title)

# --- MCP Request Handler ---
def handle_request(request_data):
    action = request_data.get('action')
    folder = request_data.get('folder')
    title = request_data.get('title')
    content = request_data.get('content')
    plain_text = request_data.get('plain_text', False) # Default to False

    # print(f"Debug: Received action: {action}, folder: {folder}, title: {title}, plain_text: {plain_text}", file=sys.stderr)
    # print(f"Debug: Content (first 50 chars): {content[:50] if content else 'None'}", file=sys.stderr)


    try:
        if action == 'create_note':
            if title is None or content is None: # Basic validation
                 raise ValueError("Missing 'title' or 'content' for create_note")
            result = create_note(folder, title, content, plain_text)
            return {"status": "success", "message": "Note created successfully.", "details": result}
        elif action == 'append_note':
            if not all([folder, title, content]):
                raise ValueError("Missing 'folder', 'title', or 'content' for append_note")
            result = append_note(folder, title, content)
            return {"status": "success", "message": "Content appended successfully.", "details": result}
        elif action == 'list_notes':
            # folder is optional for list_notes
            result = list_notes(folder)
            # Result might be a string of note titles, comma-separated. Split into a list.
            # If empty, it might return an empty string or specific "No notes found" message from AppleScript
            if result and isinstance(result, str):
                notes_list = [note.strip() for note in result.split(',') if note.strip()]
            elif not result:
                notes_list = []
            else: # Should not happen if script returns comma-separated string or empty
                notes_list = [result] # Or handle as error
            return {"status": "success", "notes": notes_list}
        elif action == 'get_note_content':
            if not all([folder, title]):
                raise ValueError("Missing 'folder' or 'title' for get_note_content")
            result = get_note_content(folder, title)
            return {"status": "success", "content_html": result}
        elif action == 'delete_note': # If exposing delete as an MCP action
            if not all([folder, title]):
                raise ValueError("Missing 'folder' or 'title' for delete_note")
            result = delete_note_by_title(folder, title)
            return {"status": "success", "message": "Note deleted successfully.", "details": result}
        else:
            raise ValueError(f"Unknown action: {action}")
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as e:
        # print(f"Error handling request: {e}", file=sys.stderr) # Log error to stderr
        return {"status": "error", "message": str(e)}
    except Exception as e: # Catch any other unexpected errors
        # print(f"Unexpected error handling request: {e}", file=sys.stderr) # Log error to stderr
        return {"status": "error", "message": f"An unexpected error occurred: {type(e).__name__} - {str(e)}"}

# --- Main Execution & Test Suite ---
if __name__ == "__main__":
    # MCP Server Mode: Read from stdin, write to stdout/stderr
    # Check if stdin is a TTY (terminal) or a pipe/redirect
    if not sys.stdin.isatty():
        try:
            raw_request = sys.stdin.read()
            # print(f"MCP Mode: Received raw request: {raw_request}", file=sys.stderr) # Debug raw input
            if not raw_request:
                # print("MCP Mode: Empty request received.", file=sys.stderr)
                error_response = {"status": "error", "message": "Empty request received."}
                print(json.dumps(error_response), file=sys.stdout) # Send error to stdout for MCP
                sys.exit(1) # Exit with error code

            request_data = json.loads(raw_request)
            response = handle_request(request_data)
            # print(f"MCP Mode: Sending response: {json.dumps(response)}", file=sys.stderr) # Debug response
            print(json.dumps(response), file=sys.stdout) # Send JSON response to stdout
        except json.JSONDecodeError:
            # print("MCP Mode: Invalid JSON received.", file=sys.stderr)
            error_response = {"status": "error", "message": "Invalid JSON format in request."}
            print(json.dumps(error_response), file=sys.stdout)
            sys.exit(1)
        except Exception as e:
            # print(f"MCP Mode: Unhandled exception: {e}", file=sys.stderr)
            error_response = {"status": "error", "message": f"Server error: {str(e)}"}
            print(json.dumps(error_response), file=sys.stdout)
            sys.exit(1)
    else:
        # Interactive/Test Mode (when run directly with a TTY)
        print("Running in Interactive/Test Mode (stdout is a TTY). For MCP, pipe input.", file=sys.stderr)
        print("This script expects JSON input via stdin when not connected to a TTY.", file=sys.stderr)
        
        # --- Test Suite ---
        # (Keep the test suite here, it will only run if __name__ == "__main__" AND stdin is a TTY)
        # print("Running test suite...", file=sys.stderr)

        # Helper for cleanup
        def cleanup_note(folder, title):
            try:
                # print(f"Cleanup: Attempting to delete note '{title}' in folder '{folder}'...", file=sys.stderr)
                delete_note_by_title(folder, title)
                # print(f"Cleanup: Successfully deleted note '{title}' in folder '{folder}'.", file=sys.stderr)
            except Exception as e:
                # print(f"Cleanup: Note '{title}' in folder '{folder}' not found or other error: {e}", file=sys.stderr)
                pass
        
        test_folder = "MCP Test Folder"
        test_title_plain = "MCP Test Note Plain"
        test_title_md = "MCP Test Note Markdown"
        test_title_append = "MCP Test Note Append"
        test_title_list = "MCP Test Note for Listing"
        test_title_get = "MCP Test Note for Get Content"
        test_title_delete = "MCP Test Note for Deletion"

        special_chars_title = "Test Note with 'Special' \"Chars\" & <Tags>"
        special_chars_folder = "Folder with 'Quotes' & \"Slashes\""
        unicode_title = "😊 Emoji Test Note" # noqa: RUF001
        empty_content_title = "Empty Content Test"
        large_content_title_plain = "Large Content Test Plain"
        large_content_title_md = "Large Content Test Markdown"


        # Cleanup existing test notes first
        # print("Initial cleanup of potential pre-existing test notes...", file=sys.stderr)
        cleanup_note(test_folder, test_title_plain)
        cleanup_note(test_folder, test_title_md)
        cleanup_note(test_folder, test_title_append)
        cleanup_note(test_folder, test_title_list + "1")
        cleanup_note(test_folder, test_title_list + "2")
        cleanup_note(test_folder, test_title_get)
        cleanup_note(test_folder, test_title_delete)
        cleanup_note(special_chars_folder, special_chars_title)
        cleanup_note(test_folder, unicode_title)
        cleanup_note(test_folder, empty_content_title)
        cleanup_note(test_folder, large_content_title_plain)
        cleanup_note(test_folder, large_content_title_md)
        # print("Initial cleanup finished.", file=sys.stderr)

        # Test data
        sample_plain_text = "This is a plain text test note created via MCP."
        sample_markdown_text = '''# Markdown Header
        **Bold Text** and *Italic Text*.
        - Item 1
        - Item 2
        ```python
        def hello():
            print("Hello, Markdown!")
        ```
        '''
        append_text_md = "\n\n## Appended Section\nThis content was appended."
        
        very_large_plain_text = "Lorum ipsum dolor sit amet..." * 1000 # Approx 28KB
        very_large_markdown_text = "# Big Doc\n" + ("- List item\n" * 2000) # Approx 26KB MD source

        # --- Test Cases (executed when run directly) ---
        try:
            # A.1: Create plain text note
            # print("\n--- Test A.1: Create Plain Text Note ---", file=sys.stderr)
            req_a1 = {"action": "create_note", "folder": test_folder, "title": test_title_plain, "content": sample_plain_text, "plain_text": True}
            res_a1 = handle_request(req_a1)
            # print(f"A.1 Response: {res_a1}", file=sys.stderr)
            assert res_a1['status'] == 'success'

            # A.2: Create Markdown note
            # print("\n--- Test A.2: Create Markdown Note ---", file=sys.stderr)
            req_a2 = {"action": "create_note", "folder": test_folder, "title": test_title_md, "content": sample_markdown_text}
            res_a2 = handle_request(req_a2)
            # print(f"A.2 Response: {res_a2}", file=sys.stderr)
            assert res_a2['status'] == 'success'
            
            # B.1: Append to Markdown note
            # print("\n--- Test B.1: Append to Markdown Note ---", file=sys.stderr)
            # First create a note to append to
            handle_request({"action": "create_note", "folder": test_folder, "title": test_title_append, "content": "Initial content."})
            req_b1 = {"action": "append_note", "folder": test_folder, "title": test_title_append, "content": append_text_md}
            res_b1 = handle_request(req_b1)
            # print(f"B.1 Response: {res_b1}", file=sys.stderr)
            assert res_b1['status'] == 'success'

            # C.1: List notes (in a specific folder)
            # print("\n--- Test C.1: List Notes ---", file=sys.stderr)
            handle_request({"action": "create_note", "folder": test_folder, "title": test_title_list + "1", "content": "Note 1 for listing."})
            handle_request({"action": "create_note", "folder": test_folder, "title": test_title_list + "2", "content": "Note 2 for listing."})
            req_c1 = {"action": "list_notes", "folder": test_folder}
            res_c1 = handle_request(req_c1)
            # print(f"C.1 Response: {res_c1}", file=sys.stderr)
            assert res_c1['status'] == 'success'
            assert isinstance(res_c1['notes'], list)
            # Check if created notes are in the list (order might vary)
            assert test_title_list + "1" in res_c1['notes'] or any((test_title_list + "1").lower() in note.lower() for note in res_c1['notes']) # case insensitive check
            assert test_title_list + "2" in res_c1['notes'] or any((test_title_list + "2").lower() in note.lower() for note in res_c1['notes'])


            # C.2: Get note content
            # print("\n--- Test C.2: Get Note Content ---", file=sys.stderr)
            handle_request({"action": "create_note", "folder": test_folder, "title": test_title_get, "content": "Content to retrieve."})
            req_c2 = {"action": "get_note_content", "folder": test_folder, "title": test_title_get}
            res_c2 = handle_request(req_c2)
            # print(f"C.2 Response: {res_c2}", file=sys.stderr)
            assert res_c2['status'] == 'success'
            assert "Content to retrieve." in res_c2['content_html'] # AppleScript might return HTML

            # C.3: Special Characters in Folder and Title
            # print("\n--- Test C.3: Special Characters in Folder and Title ---", file=sys.stderr)
            req_c3_create = {"action": "create_note", "folder": special_chars_folder, "title": special_chars_title, "content": "Content for special chars test."}
            res_c3_create = handle_request(req_c3_create)
            # print(f"C.3 Create Response: {res_c3_create}", file=sys.stderr)
            assert res_c3_create['status'] == 'success'
            
            req_c3_list = {"action": "list_notes", "folder": special_chars_folder}
            res_c3_list = handle_request(req_c3_list)
            # print(f"C.3 List Response: {res_c3_list}", file=sys.stderr)
            assert res_c3_list['status'] == 'success'
            # AppleScript might return titles slightly differently, e.g. normalized. Be flexible.
            assert any(special_chars_title.lower() in note.lower() for note in res_c3_list['notes'])


            req_c3_get = {"action": "get_note_content", "folder": special_chars_folder, "title": special_chars_title}
            res_c3_get = handle_request(req_c3_get)
            # print(f"C.3 Get Response: {res_c3_get}", file=sys.stderr)
            assert res_c3_get['status'] == 'success'
            assert "Content for special chars test." in res_c3_get['content_html']
            
            # C.4 Unicode in Title/Content
            # print("\n--- Test C.4: Unicode (Emoji) in Title and Content ---", file=sys.stderr)
            unicode_content = "This note contains an emoji 😊 and other Unicode: éàçüö." # noqa: RUF001
            req_c4_create = {"action": "create_note", "folder": test_folder, "title": unicode_title, "content": unicode_content}
            res_c4_create = handle_request(req_c4_create)
            # print(f"C.4 Create Response: {res_c4_create}", file=sys.stderr)
            assert res_c4_create['status'] == 'success'

            req_c4_get = {"action": "get_note_content", "folder": test_folder, "title": unicode_title}
            res_c4_get = handle_request(req_c4_get)
            # print(f"C.4 Get Response: {res_c4_get}", file=sys.stderr)
            assert res_c4_get['status'] == 'success'
            assert "emoji 😊" in res_c4_get['content_html'] # Check if unicode is preserved (HTML might encode it) # noqa: RUF001

            # C.5 Content Size Boundaries - Empty Content
            # print("\n--- Test C.5: Empty Content ---", file=sys.stderr)
            req_c5_create = {"action": "create_note", "folder": test_folder, "title": empty_content_title, "content": ""}
            res_c5_create = handle_request(req_c5_create)
            # print(f"C.5 Create Response: {res_c5_create}", file=sys.stderr)
            assert res_c5_create['status'] == 'success'

            req_c5_get = {"action": "get_note_content", "folder": test_folder, "title": empty_content_title}
            res_c5_get = handle_request(req_c5_get)
            # print(f"C.5 Get Response: {res_c5_get}", file=sys.stderr)
            assert res_c5_get['status'] == 'success'
            # Depending on Apple Notes, empty content might be an empty string or just the title in the body.
            # For now, just ensure it doesn't crash. The HTML might have minimal structure.
            assert res_c5_get['content_html'] is not None 

            # C.6 Content Size Boundaries - Large Content (Plain Text)
            # print("\n--- Test C.6: Large Plain Text Content ---", file=sys.stderr)
            req_c6_create = {"action": "create_note", "folder": test_folder, "title": large_content_title_plain, "content": very_large_plain_text, "plain_text": True}
            res_c6_create = handle_request(req_c6_create)
            # print(f"C.6 Create Response: {res_c6_create}", file=sys.stderr)
            assert res_c6_create['status'] == 'success'
            
            # C.7 Content Size Boundaries - Large Content (Markdown)
            # print("\n--- Test C.7: Large Markdown Content ---", file=sys.stderr)
            req_c7_create = {"action": "create_note", "folder": test_folder, "title": large_content_title_md, "content": very_large_markdown_text}
            res_c7_create = handle_request(req_c7_create)
            # print(f"C.7 Create Response: {res_c7_create}", file=sys.stderr)
            assert res_c7_create['status'] == 'success'

            # D.1: Delete note (if exposed as an action, otherwise this is for cleanup)
            # print("\n--- Test D.1: Delete Note ---", file=sys.stderr)
            handle_request({"action": "create_note", "folder": test_folder, "title": test_title_delete, "content": "Note to be deleted."})
            req_d1 = {"action": "delete_note", "folder": test_folder, "title": test_title_delete}
            res_d1 = handle_request(req_d1)
            # print(f"D.1 Response: {res_d1}", file=sys.stderr)
            assert res_d1['status'] == 'success'
            
            # Verify deletion by trying to get it (should fail or return empty)
            try:
                get_deleted_note_res = handle_request({"action": "get_note_content", "folder": test_folder, "title": test_title_delete})
                # print(f"Attempt to get deleted note response: {get_deleted_note_res}", file=sys.stderr)
                assert get_deleted_note_res['status'] == 'error' # Expecting an error or empty content
            except ValueError as e: # AppleScript might raise error if note not found
                # print(f"Successfully confirmed note deletion (ValueError): {e}", file=sys.stderr)
                pass


            print("\nAll direct execution tests passed!", file=sys.stderr)

        except AssertionError as e:
            print(f"Test failed: {e}", file=sys.stderr)
        except Exception as e:
            print(f"An error occurred during tests: {e}", file=sys.stderr)
        finally:
            # print("\nFinal cleanup of test notes...", file=sys.stderr)
            cleanup_note(test_folder, test_title_plain)
            cleanup_note(test_folder, test_title_md)
            cleanup_note(test_folder, test_title_append)
            cleanup_note(test_folder, test_title_list + "1")
            cleanup_note(test_folder, test_title_list + "2")
            cleanup_note(test_folder, test_title_get)
            # test_title_delete should already be gone
            cleanup_note(special_chars_folder, special_chars_title)
            cleanup_note(test_folder, unicode_title)
            cleanup_note(test_folder, empty_content_title)
            cleanup_note(test_folder, large_content_title_plain)
            cleanup_note(test_folder, large_content_title_md)
            # print("Final cleanup finished.", file=sys.stderr)
'''