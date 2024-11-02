from collections import defaultdict
from pathlib import Path
from typing import Literal, get_args

from locify.editor.exceptions import ToolError
from locify.editor.results import CLIResult, ToolResult

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

    name = 'oh_editor'

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
                raise ToolError('Parameter `file_text` is required for command: create')
            self.write_file(_path, file_text)
            self._file_history[_path].append(file_text)
            return ToolResult(output=f'File created successfully at: {_path}')
        elif command == 'str_replace':
            if not old_str:
                raise ToolError(
                    'Parameters `old_str` is required for command: str_replace'
                )
            return self.str_replace(_path, old_str, new_str)
        elif command == 'insert':
            if insert_line is None:
                raise ToolError(
                    'Parameter `insert_line` is required for command: insert'
                )
            if not new_str:
                raise ToolError('Parameter `new_str` is required for command: insert')
            return self.insert(_path, insert_line, new_str)
        elif command == 'undo_edit':
            return self.undo_edit(_path)

        raise ToolError(
            f'Unrecognized command {command}. The allowed commands for the {self.name} tool are: {", ".join(get_args(Command))}'
        )

    def str_replace(self, path: Path, old_str: str, new_str: str | None) -> CLIResult:
        """
        Implement the str_replace command, which replaces old_str with new_str in the file content.
        """
        # TODO:
        raise NotImplementedError

    def validate_path(self, command: Command, path: Path) -> None:
        """
        Check that the path/command combination is valid.
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
        # TODO:
        raise NotImplementedError

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

    def _make_output(self, file_content: str, file_descriptor: str) -> str:
        """
        Generate output for the CLI based on the content of a file.
        """
        # TODO:
        raise NotImplementedError
