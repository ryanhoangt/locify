class Prompts:
    repo_content_prefix = """Below are a tree of classes and functions for files in the workspace. It's chosen based on some heuristics and is not always extensive. So, please only use them for quick code navigation and not as a definitive source of truth:\n\n"""

    def_prefix = """Since some identifiers (class, functions) are mentioned, here are definitions of those identifiers, which can be useful to quickly locate where they might be defined (Note that if the assistant find those definitions are not relevant, a search can be performed in the workspace yourself):\n"""

    direct_ref_prefix = """Because some identifiers (class, functions) are mentioned, here are some direct references to those identifiers, which can be useful for understanding how the codebase is connected:\n"""

    nav_only_reminder = """Please only use those for quick code navigation and not as a definitive source of truth. If you need more information, please search in the workspace yourself.\n"""
