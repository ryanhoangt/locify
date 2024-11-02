from dataclasses import dataclass


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""

    output: str | None = None
    ...  # TODO: implement the ToolResult class


class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""
