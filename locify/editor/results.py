from dataclasses import dataclass, fields

from locify.editor.config import MAX_RESPONSE_LEN_CHAR
from locify.editor.prompts import CONTENT_TRUNCATED_NOTICE


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""

    output: str | None = None
    error: str | None = None
    # TODO: implement the ToolResult class

    def __bool__(self):
        return any(getattr(self, field.name) for field in fields(self))


class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""


def maybe_truncate(
    content: str, truncate_after: int | None = MAX_RESPONSE_LEN_CHAR
) -> str:
    """
    Truncate content and append a notice if content exceeds the specified length.
    """
    return (
        content
        if not truncate_after or len(content) <= truncate_after
        else content[:truncate_after] + CONTENT_TRUNCATED_NOTICE
    )
