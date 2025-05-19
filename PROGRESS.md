## Project Progress: applenote_mcp

### Stage 1: Core MCP and Plain Text Note Creation (COMPLETED)
- **Objective**: Basic Python wrapper (`mcp_handler.py`) to call a simple AppleScript (`create_note_basic.scpt`) for creating plain text notes in the default Notes folder. Basic unit tests.
- **Status**: COMPLETED
- **Key Learnings**:
    - Handling `mcp_filesystem_create_directory` vs. `run_terminal_cmd` for directory creation.
    - Importance of absolute paths for `mcp_filesystem_write_file`.
    - Correcting f-string syntax and `unittest` invocation.

### Stage 2: Specified Folders, Titles, and Basic Markdown (COMPLETED)
- **Objective**: Enhance AppleScript (`create_note_advanced.scpt`) for specified folders and titles. Update `mcp_handler.py` for these parameters and basic Markdown-to-HTML conversion (with graceful degradation).
- **Status**: COMPLETED
- **Key Learnings**:
    - Python `sys.path` and import resolution for tests (`tests/__init__.py`, `python3 -m unittest discover`).
    - Debugging issues related to file versions and ensuring the correct script is loaded.
    - Apple Notes' behavior with empty titles (uses first line of content).

### Stage 3: Append to Note (COMPLETED)
- **Objective**: Implement appending content (plain text or Markdown-converted HTML) to existing notes, identified by title and optional folder. AppleScript `append_to_note.scpt`.
- **Status**: COMPLETED
- **Key Learnings**:
    - Importance of correct argument order between Python and AppleScript.
    - AppleScript error handling for "note not found" vs. "multiple notes found".
    - Confirmed Markdown-to-HTML append functionality.

### Stage 4: List Notes and Read Note Content (COMPLETED)
- **Objective**:
    1.  `list_notes.scpt`: List note titles from a specified folder (or all notes).
    2.  `get_note_content.scpt`: Get the body (HTML content) of a uniquely identified note.
    3.  Update `mcp_handler.py` and tests for these actions.
- **Status**: COMPLETED
- **Key Achievements**:
    - Successfully implemented `list_notes` and `get_note_content` functionalities.
    - Introduced a `delete_note_by_title.scpt` utility and integrated it into the Python test suite (`mcp_handler.py`) for robust test environment cleanup. This resolved previous issues with duplicate notes caused by repeated test runs.
    - Significantly improved Markdown handling:
        - Ensured consistent use of `python-markdown` extensions (`['fenced_code', 'tables', 'nl2br']`).
        - Refined `markdown` module state management within tests to prevent inconsistencies.
        - Corrected Markdown input strings (removed leading newlines) which resolved major parsing issues. Titles (`#`, `##`) and standard lists (`- item`) are now correctly converted to their HTML equivalents.
        - The test suite in `mcp_handler.py` is now more comprehensive and reliable due to the cleanup logic.
- **Known Minor Issues/TODOs**:
    - The `delete_note_by_title.scpt` script shows an error (`"Notes"遇到一个错误：不能获得"account "On My Mac""。 (-1728)`) when attempting to clean notes from the default Notes location if the "On My Mac" account is the target. This does not affect core functionality for iCloud notes or notes in specified folders.
    - `python-markdown` (with current extensions) does not convert lists immediately following a heading (e.g. `## Title\n* Item`) or ordered lists (e.g. `1. Item`) into HTML lists; they are treated as part of the heading's text or plain text. Users can ensure an empty line between headings and lists in their Markdown for proper list rendering. This is a minor formatting detail.

### Stage 5: AppleScript Robustness & Boundary Testing (COMPLETED via Python integration tests)
- **Objective**: Enhance Python-level integration tests to cover more edge cases for AppleScript interactions, including special characters, Unicode, folder name variations, and content size limits. This effectively serves as robust testing for the AppleScripts themselves.
- **Status**: COMPLETED
- **Key Achievements**:
    - Successfully tested creation, appending, listing, and fetching of notes with:
        - Special characters (`'"&<>`) in titles and content.
        - Unicode characters (Emoji 😊) in titles and content.
        - Complex Markdown structures.
        - Folder names containing special characters.
        - Empty content and very large content (approx. 50-60KB).
    - All tests included appropriate cleanup steps to ensure test atomicity.

### Stage 6: MCP Service Integration (COMPLETED)
- **Objective**: Transform `mcp_handler.py` into a proper MCP service that accepts JSON requests via stdin and returns JSON responses via stdout. Create `mcp.json` for service definition.
- **Status**: COMPLETED
- **Sub-stages**:
    - **S6.1: `mcp_handler.py` MCP Service Transformation (COMPLETED)**
        - **Description**: Refactored `mcp_handler.py` to handle JSON-RPC like requests, manage `stdin`/`stdout`/`stderr` appropriately, and include a self-contained test suite runnable with `--run-tests`. Successfully fixed all linting and indentation issues, and internal tests are passing.
        - **Status**: COMPLETED
    - **S6.2: Create `mcp.json` configuration file (COMPLETED)**
        - **Description**: Defined the service capabilities, commands, arguments, and invocation method in `mcp.json`.
        - **Status**: COMPLETED

### Stage 7: Code Refinement, Documentation, and Advanced Formatting (Planned)
- **Objective**: General code cleanup, add comprehensive docstrings, refine `README.md` and `DESIGN.md`. Explore any remaining advanced formatting options for notes.
- **Status**: Planned
