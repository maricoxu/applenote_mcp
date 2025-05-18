import unittest
import io
import sys
from unittest.mock import patch, MagicMock
import os

# Ensure src is in path for importing mcp_handler
# This needs to be robust for how unittest discovers and loads tests.
# A common way is to ensure the test runner (e.g., 'python -m unittest discover')
# is run from a directory where 'src' is discoverable, or by structuring
# the project as a proper package.

# Let's assume the standard 'python -m unittest discover tests' from project root.
# The __init__.py in 'tests' and 'src' (if it existed) would help.
# The sys.path manipulation below is generally reliable when the test file itself is executed
# or when unittest loads it directly.

# Get the absolute path to the 'src' directory
# __file__ is tests/test_mcp_handler.py
# script_dir is tests/
# parent_dir is applenote_mcp/
# src_dir is applenote_mcp/src/
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
src_dir = os.path.join(parent_dir, "src")

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Now import from mcp_handler
# from src.mcp_handler import handle_request
from src import mcp_handler
print(f"DEBUG: Imported mcp_handler: {mcp_handler}")
print(f"DEBUG: dir(mcp_handler): {dir(mcp_handler)}")


# Mock a markdown library if the real one isn't available or for consistent testing
class MockMarkdownLib:
    def markdown(self, text, extensions=None):
        # Simple mock, real conversion might produce more complex HTML
        return f"<html><body>{text} (processed by mock markdown)</body></html>"

# Attempt to import the real markdown library to see if it exists on the system
try:
    import markdown as real_markdown_lib_for_setup
except ImportError:
    real_markdown_lib_for_setup = None


class TestMCPHandlerStage2(unittest.TestCase):

    def setUp(self):
        # Redirect stdout to capture print statements from handle_request
        self.captured_output = io.StringIO()
        sys.stdout = self.captured_output
        # Ensure mcp_handler.markdown is reset before each test
        # It will be patched specifically within tests that need to control it
        if mcp_handler: # Ensure mcp_handler module was imported
            mcp_handler.markdown = real_markdown_lib_for_setup


    def tearDown(self):
        # Restore stdout
        sys.stdout = sys.__stdout__
        # Restore mcp_handler.markdown to its original state after all tests in the class
        if mcp_handler: # Ensure mcp_handler module was imported
            mcp_handler.markdown = real_markdown_lib_for_setup

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    def test_create_note_plain_text_with_folder_and_title(self, mock_os_exists, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout="Success from AppleScript: plain text", returncode=0, stderr="")
        
        response = mcp_handler.handle_request(
            action="create_note", 
            content="Plain text content", 
            title="My Plain Note", 
            folder="My Test Folder", 
            input_format="text"
        )
        
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0] # Get the list of command arguments
        
        self.assertEqual(call_args[0], "osascript")
        self.assertTrue(call_args[1].endswith("create_note_advanced.scpt"))
        self.assertEqual(call_args[2], "Plain text content") # processed_content
        self.assertEqual(call_args[3], "My Plain Note")      # effective_title
        self.assertEqual(call_args[4], "My Test Folder")     # effective_folder
        
        self.assertIn("Success: Note 'My Plain Note' processed.", response)
        self.assertIn("Success from AppleScript: plain text", response)
        self.assertNotIn("WARN: Markdown to HTML conversion failed", self.captured_output.getvalue())
        self.assertNotIn("WARN: `markdown` library not installed", self.captured_output.getvalue())

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    def test_create_note_markdown_conversion_success(self, mock_os_exists, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout="Success from AppleScript: markdown", returncode=0, stderr="")
        
        # Patch mcp_handler.markdown to use our MockMarkdownLib for this test
        with patch.object(mcp_handler, 'markdown', MockMarkdownLib()):
            response = mcp_handler.handle_request(
                action="create_note", 
                content="# Markdown Header", 
                title="My Markdown Note", 
                folder="Markdown Folder", 
                input_format="markdown"
            )
        
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        
        expected_html = "<html><body># Markdown Header (processed by mock markdown)</body></html>"
        self.assertEqual(call_args[2], expected_html) # Check HTML content
        self.assertEqual(call_args[3], "My Markdown Note")
        self.assertEqual(call_args[4], "Markdown Folder")
        
        self.assertIn("INFO: Content converted from Markdown to HTML", self.captured_output.getvalue())
        self.assertIn("Success: Note 'My Markdown Note' processed.", response)

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    def test_create_note_markdown_conversion_library_missing(self, mock_os_exists, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout="Success from AppleScript: md lib missing", returncode=0, stderr="")
        
        # Patch mcp_handler.markdown to be None for this test
        with patch.object(mcp_handler, 'markdown', None):
            response = mcp_handler.handle_request(
                action="create_note", 
                content="# Raw Markdown", 
                title="Raw MD Note", 
                folder="Raw Folder", 
                input_format="markdown" # Still requesting markdown
            )
            
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        
        self.assertEqual(call_args[2], "# Raw Markdown") # Should be raw content
        
        self.assertIn("WARN: `markdown` library not installed", self.captured_output.getvalue())
        self.assertIn("Success: Note 'Raw MD Note' processed.", response)

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    def test_create_note_markdown_conversion_failure(self, mock_os_exists, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout="Success from AppleScript: md conversion fail", returncode=0, stderr="")
        
        # Mock the markdown conversion to raise an exception
        mock_md_lib = MockMarkdownLib()
        mock_md_lib.markdown = MagicMock(side_effect=Exception("Conversion Error"))

        with patch.object(mcp_handler, 'markdown', mock_md_lib):
            response = mcp_handler.handle_request(
                action="create_note",
                content="Problematic MD",
                title="MD Fail Note",
                folder="Fail Folder",
                input_format="markdown"
            )

        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        self.assertEqual(call_args[2], "Problematic MD") # Should be raw content after failure

        self.assertIn("WARN: Markdown to HTML conversion failed: Conversion Error", self.captured_output.getvalue())
        self.assertIn("Success: Note 'MD Fail Note' processed.", response)


    @patch('os.path.exists', return_value=False)
    def test_apple_script_not_found(self, mock_os_exists):
        response = mcp_handler.handle_request(action="create_note", content="Any content", title="Any title")
        self.assertTrue(response.startswith("Error: Script"))
        self.assertIn("WARN: AppleScript file not found", self.captured_output.getvalue())

    def test_unknown_action(self):
        response = mcp_handler.handle_request(action="delete_everything", content="", title="")
        self.assertTrue(response.startswith("Error: Action 'delete_everything' not recognized"))
        self.assertIn("WARN: Action 'delete_everything' is not recognized.", self.captured_output.getvalue())

    @patch('subprocess.run')
    @patch('os.path.exists', return_value=True)
    def test_create_note_empty_title(self, mock_os_exists, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout="Success from AppleScript: empty title", returncode=0, stderr="")
        
        response = mcp_handler.handle_request(
            action="create_note", 
            content="Content for empty title note", 
            title="", # Empty title
            folder="Test Folder", 
            input_format="text"
        )
        
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        
        self.assertEqual(call_args[3], "") # effective_title should be empty
        
        # The success message uses 'Untitled' if title is empty in handle_request's return formatting
        self.assertIn("Success: Note 'Untitled' processed.", response)

if __name__ == '__main__':
    unittest.main()
