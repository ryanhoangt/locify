from collections import defaultdict
from pathlib import Path
from typing import Literal

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
        else:
            # TODO:
            ...
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
