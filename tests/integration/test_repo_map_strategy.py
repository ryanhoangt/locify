import subprocess
from pathlib import Path

import pytest

from locify.indexing.repo_map.strategy import RepoMapStrategy
from locify.tree_sitter.parser import TagKind
from locify.utils.llm import get_token_count_from_text


# Helper function to run shell commands in the temp repo
def run_git_command(repo_path: Path, command: list[str]):
    subprocess.run(command, cwd=repo_path, check=True)


@pytest.fixture
def setup_git_repo_with_no_refs(tmp_path):
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


@pytest.fixture
def setup_git_repo_with_refs(tmp_path):
    # Set up a temporary Git repository
    repo_path = tmp_path / 'repo'
    repo_path.mkdir()

    # Initialize git repository
    run_git_command(repo_path, ['git', 'init'])

    # Create some files in the repo
    def_file = repo_path / 'test_file1.py'
    ref_file = repo_path / 'test_file2.py'

    def_file.write_text('def foo():\n    pass\n\ndef bar():\n    pass\n')
    ref_file.write_text('from test_file1 import foo, bar\n\nfoo()\nbar()\n')

    # Stage and commit the files
    run_git_command(repo_path, ['git', 'add', '.'])
    run_git_command(repo_path, ['git', 'commit', '-m', 'Initial commit'])

    return repo_path


def test_repo_map_strategy_get_ranked_tags_with_no_refs(setup_git_repo_with_no_refs):
    repo_path = setup_git_repo_with_no_refs

    # Initialize the RepoMapStrategy with the temp repo
    strategy = RepoMapStrategy(root=str(repo_path))

    # Generate the ranked tags with an empty mentioned_rel_files and mentioned_idents
    ranked_tags = strategy.get_ranked_tags()

    # Ensure the output has some ranked tags
    assert len(ranked_tags) == 0


def test_repo_map_strategy_get_ranked_tags_with_refs(setup_git_repo_with_refs):
    repo_path = setup_git_repo_with_refs

    # Initialize the RepoMapStrategy with the temp repo
    strategy = RepoMapStrategy(root=str(repo_path))

    # Generate the ranked tags with an empty mentioned_rel_files and mentioned_idents
    ranked_tags = strategy.get_ranked_tags()

    # Ensure the output has some ranked tags
    assert len(ranked_tags) > 0

    # Check if the tags contain the correct file names and tag kinds
    tag_files = {tag.rel_path for tag in ranked_tags}
    assert 'test_file1.py' in tag_files
    assert 'test_file2.py' in tag_files

    # Check if some tags are marked as definitions
    def_tags = [tag for tag in ranked_tags if tag.tag_kind == TagKind.DEF]
    assert len(def_tags) > 0

    # Generate the full map using the base method
    repo_map = strategy.get_map()

    # Check if the map_output contains expected file names
    assert 'test_file1.py' in repo_map
    assert 'test_file2.py' in repo_map

    # Check token count from the map
    token_count = get_token_count_from_text(strategy.model_name, repo_map)

    # Ensure the token count is a reasonable positive integer
    assert token_count > 0

    repo_content_prefix = strategy.content_prefix
    expected_map = (
        repo_content_prefix
        + """test_file1.py:
  1│def foo():
...⋮...
  4│def bar():
...⋮...
test_file2.py:
...⋮..."""
    )
    assert repo_map == expected_map
