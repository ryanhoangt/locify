from pathlib import Path

from git import Repo


class GitRepoUtils:
    
    def __init__(self, repo_path: str) -> None:
        self.repo_path = Path(repo_path)
        try:
            self.repo = Repo(self.repo_path)
        except:
            raise Exception(f"Could not find git repository at {repo_path}")
    
    def get_all_absolute_tracked_files(self) -> list[str]:
        return [str(self.repo_path / item.path) for item in self.repo.tree().traverse() if item.type == 'blob']
    
    def get_all_absolute_staged_files(self) -> list[str]:
        return [str(self.repo_path / item.a_path) for item in self.repo.index.diff("HEAD")]
    
    def get_absolute_tracked_files_in_directory(self, rel_dir_path: str) -> list[str]:
        rel_dir_path = rel_dir_path.rstrip('/')
        return [str(self.repo_path / item.path) for item in self.repo.tree().traverse() if item.path.startswith(rel_dir_path + '/') and item.type == 'blob']