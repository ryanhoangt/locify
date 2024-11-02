from collections import defaultdict
from pathlib import Path
from typing import Literal, get_args

from locify.editor.exceptions import (
    EditorToolParameterInvalidError,
    EditorToolParameterMissingError,
    ToolError,
)
from locify.editor.results import CLIResult, ToolResult
from locify.utils.file import read_file

Command = Literal[
    'view',
    'create',
    'str_replace',
    'insert',
    'undo_edit',
    # 'jump_to_definition', TODO:
    # 'find_references' TODO:
]


class OHEditor:
    """
    An filesystem editor tool that allows the agent to
    - view
    - create
    - navigate
    - edit files
    The tool parameters are defined by Anthropic and are not editable.

    Original implementation: https://github.com/anthropics/anthropic-quickstarts/blob/main/computer-use-demo/computer_use_demo/tools/edit.py
    """

    TOOL_NAME = 'oh_editor'
    SNIPPET_LINES = 4

    def __init__(self) -> None:
        self._file_history: dict[Path, list[str]] = defaultdict(list)

    def __call__(
        self,
        *,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        **kwargs,
    ) -> ToolResult | CLIResult:
        _path = Path(path)
        self.validate_path(command, _path)
        if command == 'view':
            return self.view(_path, view_range)
        elif command == 'create':
            if not file_text:
                raise
            self.write_file(_path, file_text)
            self._file_history[_path].append(file_text)
            return ToolResult(output=f'File created successfully at: {_path}')
        elif command == 'str_replace':
            if not old_str:
                raise EditorToolParameterMissingError(command, 'old_str')
            return self.str_replace(_path, old_str, new_str)
        elif command == 'insert':
            if insert_line is None:
                raise EditorToolParameterMissingError(command, 'insert_line')
            if not new_str:
                raise EditorToolParameterMissingError(command, 'new_str')
            return self.insert(_path, insert_line, new_str)
        elif command == 'undo_edit':
            return self.undo_edit(_path)

        raise ToolError(
            f'Unrecognized command {command}. The allowed commands for the {self.TOOL_NAME} tool are: {", ".join(get_args(Command))}'
        )

    def str_replace(self, path: Path, old_str: str, new_str: str | None) -> CLIResult:
        """
        Implement the str_replace command, which replaces old_str with new_str in the file content.
        """
        # TODO:
        raise NotImplementedError

    def view(self, path: Path, view_range: list[int] | None = None) -> CLIResult:
        """
        View the contents of a file or a directory.
        """
        # TODO:
        raise NotImplementedError

    def write_file(self, path: Path, file_text: str) -> None:
        """
        Write the content of a file to a given path; raise a ToolError if an error occurs.
        """
        # TODO:
        raise NotImplementedError

    def insert(self, path: Path, insert_line: int, new_str: str) -> CLIResult:
        """
        Implement the insert command, which inserts new_str at the specified line in the file content.
        """
        try:
            file_text = read_file(path)
        except Exception as e:
            raise ToolError(f'Ran into {e} while trying to read {path}') from None

        file_text = file_text.expandtabs()
        new_str = new_str.expandtabs()

        file_text_lines = file_text.split('\n')
        num_lines = len(file_text_lines)

        if insert_line < 0 or insert_line > num_lines:
            raise EditorToolParameterInvalidError(
                'insert_line',
                insert_line,
                f'It should be within the range of lines of the file: {[0, num_lines]}',
            )

        new_str_lines = new_str.split('\n')
        new_file_text_lines = (
            file_text_lines[:insert_line]
            + new_str_lines
            + file_text_lines[insert_line:]
        )
        snippet_lines = (
            file_text_lines[max(0, insert_line - self.SNIPPET_LINES) : insert_line]
            + new_str_lines
            + file_text_lines[
                insert_line : min(num_lines, insert_line + self.SNIPPET_LINES)
            ]
        )
        new_file_text = '\n'.join(new_file_text_lines)
        snippet = '\n'.join(snippet_lines)

        self.write_file(path, new_file_text)
        self._file_history[path].append(new_file_text)

        success_message = f'The file {path} has been edited. '
        success_message += self._make_output(
            snippet,
            'a snippet of the edited file',
            max(1, insert_line - self.SNIPPET_LINES + 1),
        )
        success_message += 'Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary.'
        return CLIResult(output=success_message)

    def validate_path(self, command: Command, path: Path) -> None:
        """
        Check that the path/command combination is valid.
        """
        # Check if its an absolute path
        if not path.is_absolute():
            suggested_path = Path('') / path
            raise EditorToolParameterInvalidError(
                'path',
                path,
                f'The path should be an absolute path, starting with `/`. Maybe you meant {suggested_path}?',
            )
        # Check if path and command are compatible
        if command == 'create' and path.exists():
            raise EditorToolParameterInvalidError(
                'path',
                path,
                f'File already exists at: {path}. Cannot overwrite files using command `create`.',
            )
        if command != 'create' and not path.exists():
            raise EditorToolParameterInvalidError(
                'path',
                path,
                f'The path {path} does not exist. Please provide a valid path.',
            )
        if command != 'view' and path.is_dir():
            raise EditorToolParameterInvalidError(
                'path',
                path,
                f'The path {path} is a directory and only the `view` command can be used on directories.',
            )

    def undo_edit(self, path: Path) -> CLIResult:
        """
        Implement the undo_edit command.
        """
        if not self._file_history[path]:
            raise ToolError(f'No edit history found for {path}.')

        old_text = self._file_history[path].pop()
        self.write_file(path, old_text)

        return CLIResult(
            output=f'Last edit to {path} undone successfully. {self._make_output(old_text, str(path))}'
        )

    def _make_output(
        self,
        snippet_content: str,
        snippet_description: str,
        start_line: int = 1,
        expand_tabs: bool = True,
    ) -> str:
        """
        Generate output for the CLI based on the content of a code snippet.
        """
        # TODO:
        raise NotImplementedError
        raise NotImplementedError
