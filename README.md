# Locify 🔎 [![PyPI](https://img.shields.io/pypi/pyversions/locify.svg?style=plastic)](https://github.com/ryanhoangt/locify)

*Locify* is a library designed to help LLM-based agents navigate and analyze large codebases efficiently. It leverages parsing techniques to provide insights into code structure and relationships.

## Features

On a *Git-based* repository, *Locify* offers:

- **Codebase Skeleton Mapping**:
  - [`FullMapStrategy`](locify/indexing/full_map/README.md): Generates a skeleton map of the entire codebase or a directory only.
  - [`RepoMapStrategy`](locify/indexing/repo_map/README.md): Focuses on the reference relationships, using graph theory to rank and analyze code elements.

- **Tree-sitter Integration**: Utilizes Tree-sitter for precise parsing of source code, supporting multiple programming languages.

- **Command-Line Interface**: Provides a user-friendly CLI for executing different mapping strategies.

## Installation

*Locify* can be installed via pip:

```bash
pip install locify
```

## Usage

### Command-Line Interface

Locify offers a CLI to execute mapping strategies:

```bash
python -m locify.cli <strategy> [options]
```

- `<strategy>`: Choose between `fullmap` and `repomap`.
- `[options]`: Additional options for customizing the mapping process.

### Example

To generate a full map of a codebase:

```bash
python -m locify.cli fullmap get_map_with_token_count --root /path/to/gitrepo
```

## Development

### Directory Structure

- `locify/`: Main source code directory.
  - `cli.py`: Command-line interface implementation.
  - `indexing/`: Contains strategies for code mapping.
    - `full_map/`: Implementation of `FullMapStrategy`.
    - `repo_map/`: Implementation of `RepoMapStrategy`.
  - `tree_sitter/`: Tree-sitter integration for parsing.
    - `parser.py`: Tree-sitter parser implementation.
    - `queries/`: Schema query files for different languages.
  - `utils/`: Utility functions and classes.

### Testing

Tests are located in the `tests` directory. Run tests using:

```bash
poetry run pytest
```

## Acknowledgements

This project was inspired by the [aider's RepoMap implementation](https://github.com/paul-gauthier/aider/blob/main/aider/repomap.py).

## License

This project is licensed under the terms of the MIT license. See the [LICENSE](LICENSE) file for details.
