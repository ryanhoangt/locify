from pathlib import Path

import pytest
from git import Repo

from locify.utils.file import GitRepoUtils


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository with some test files."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git repo
    repo = Repo.init(repo_dir)
    
    # Create some test files and directories
    (repo_dir / "file1.txt").write_text("content1")
    (repo_dir / "file2.txt").write_text("content2")
    
    # Create a subdirectory with files
    test_dir = repo_dir / "test_dir"
    test_dir.mkdir()
    (test_dir / "file3.txt").write_text("content3")
    (test_dir / "file4.txt").write_text("content4")
    
    # Stage and commit initial files
    repo.index.add(["file1.txt", "file2.txt", "test_dir/file3.txt", "test_dir/file4.txt"])
    repo.index.commit("Initial commit")
    
    # Create an unstaged file
    (repo_dir / "unstaged.txt").write_text("unstaged")
    
    # Create a staged but not committed file
    (repo_dir / "staged.txt").write_text("staged")
    repo.index.add(["staged.txt"])
    
    return repo_dir

@pytest.fixture
def git_utils(temp_git_repo):
    """Create a GitRepoUtils instance with the temporary repository."""
    return GitRepoUtils(str(temp_git_repo))

def test_init_valid_repo(temp_git_repo):
    """Test initialization with a valid repository."""
    utils = GitRepoUtils(str(temp_git_repo))
    assert utils.repo_path == Path(temp_git_repo)
    assert utils.repo is not None

def test_init_invalid_repo(tmp_path):
    """Test initialization with an invalid repository path."""
    invalid_path = tmp_path / "nonexistent"
    with pytest.raises(Exception) as exc_info:
        GitRepoUtils(str(invalid_path))
    assert "Could not find git repository" in str(exc_info.value)

def test_get_all_tracked_files(git_utils):
    """Test getting all tracked files."""
    tracked_files = git_utils.get_all_tracked_files()
    
    # Check if all expected files are present
    expected_files = {
        "file1.txt",
        "file2.txt",
        "test_dir/file3.txt",
        "test_dir/file4.txt"
    }
    assert set(tracked_files) == expected_files
    
    # Verify that unstaged and untracked files are not included
    assert "unstaged.txt" not in tracked_files

def test_get_all_staged_files(git_utils):
    """Test getting all staged files."""
    staged_files = git_utils.get_all_staged_files()
    
    # Only staged.txt should be in the staged files list
    assert "staged.txt" in staged_files
    assert "file1.txt" not in staged_files  # Already committed
    assert "unstaged.txt" not in staged_files  # Not staged

def test_get_tracked_files_in_directory(git_utils):
    """Test getting tracked files in a specific directory."""
    # Test files in test_dir
    test_dir_files = git_utils.get_tracked_files_in_directory("test_dir")
    expected_files = {"test_dir/file3.txt", "test_dir/file4.txt"}
    assert set(test_dir_files) == expected_files
    
    # Test files in root directory (should be empty when specifying a non-existent directory)
    nonexistent_dir_files = git_utils.get_tracked_files_in_directory("nonexistent")
    assert len(nonexistent_dir_files) == 0

def test_get_tracked_files_in_directory_with_trailing_slash(git_utils):
    """Test getting tracked files in a directory with trailing slash."""
    test_dir_files = git_utils.get_tracked_files_in_directory("test_dir/")
    expected_files = {"test_dir/file3.txt", "test_dir/file4.txt"}
    assert set(test_dir_files) == expected_files

def test_get_tracked_files_in_subdirectory(git_utils):
    """Test getting tracked files in a subdirectory."""
    # Test files in test_dir
    test_dir_files = git_utils.get_tracked_files_in_directory("test_dir")
    expected_files = {"test_dir/file3.txt", "test_dir/file4.txt"}
    assert set(test_dir_files) == expected_files

def test_empty_directory(git_utils, temp_git_repo):
    """Test getting tracked files in an empty directory."""
    # Create an empty directory
    empty_dir = temp_git_repo / "empty_dir"
    empty_dir.mkdir()
    
    files = git_utils.get_tracked_files_in_directory("empty_dir")
    assert len(files) == 0