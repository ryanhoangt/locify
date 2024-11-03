from locify.editor.editor import Command, OHEditor
from locify.editor.exceptions import ToolError
from locify.editor.results import ToolResult

_GLOBAL_EDITOR = OHEditor()


def _make_api_tool_result(
    tool_result: ToolResult,
) -> str:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: str = ''
    is_error = False
    if tool_result.error:
        is_error = True
        tool_result_content = tool_result.error
    else:
        assert tool_result.output, 'Expecting output in file_editor.'
        tool_result_content = tool_result.output
    if is_error:
        return f'ERROR:\n{tool_result_content}'
    else:
        return tool_result_content


def file_editor(
    command: Command,
    path: str,
    file_text: str | None = None,
    view_range: list[int] | None = None,
    old_str: str | None = None,
    new_str: str | None = None,
    insert_line: int | None = None,
) -> str:
    try:
        result = _GLOBAL_EDITOR(
            command=command,
            path=path,
            file_text=file_text,
            view_range=view_range,
            old_str=old_str,
            new_str=new_str,
            insert_line=insert_line,
        )
    except ToolError as e:
        return _make_api_tool_result(ToolResult(error=e.message))

    return _make_api_tool_result(result)


__all__ = ['file_editor']
