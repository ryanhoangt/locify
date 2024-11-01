from dataclasses import dataclass


@dataclass
class ToolResult:
    output: str | None = None
    ...  # TODO: implement the ToolResult class


class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""
