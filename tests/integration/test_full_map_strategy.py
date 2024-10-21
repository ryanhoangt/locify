import subprocess
from pathlib import Path

import pytest

from locify.indexing.full_map.strategy import FullMapStrategy
from locify.utils.llm import get_token_count_from_text


# Helper function to run shell commands in the temp repo
def run_git_command(repo_path: Path, command: list[str]):
    subprocess.run(command, cwd=repo_path, check=True)


@pytest.fixture
def setup_git_repo(tmp_path):
    # Set up a temporary Git repository
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()

    # Initialize git repository
    run_git_command(repo_path, ['git', 'init'])

    # Create some files in the repo
    file1 = repo_path / 'test_file1.py'
    file2 = repo_path / 'test_file2.py'

    file1.write_text('def foo():\n    pass\n')
    file2.write_text('def bar():\n    pass\n')

    # Stage and commit the files
    run_git_command(repo_path, ['git', 'add', '.'])
    run_git_command(repo_path, ['git', 'commit', '-m', 'Initial commit'])

    return repo_path


# Test for FullMapStrategy integration with real git repo
def test_full_map_strategy_integration(setup_git_repo):
    repo_path = setup_git_repo

    # Initialize the FullMapStrategy with the temp repo
    strategy = FullMapStrategy(root=str(repo_path))

    # Generate the map
    map_output = strategy.get_map()

    # Check if the map_output contains expected file names
    assert 'test_file1.py' in map_output
    assert 'test_file2.py' in map_output

    # Check token count from the map
    token_count = get_token_count_from_text(strategy.model_name, map_output)

    # Ensure the token count is a reasonable positive integer
    assert token_count > 0
