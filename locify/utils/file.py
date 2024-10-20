from pathlib import Path

from git import Repo


class GitRepoUtils:
    
    def __init__(self, repo_path: str) -> None:
        self.repo_path = Path(repo_path)
        try:
            self.repo = Repo(self.repo_path)
        except:
            raise Exception(f"Could not find git repository at {repo_path}")
    
    def get_all_tracked_files(self) -> list[str]:
        return [
            item.path for item in self.repo.tree().traverse() 
            if item.type == 'blob'  # This checks if it's a file (blob) and not a directory
        ]
    
    def get_all_staged_files(self) -> list[str]:
        return [item.a_path for item in self.repo.index.diff("HEAD")]
    
    def get_tracked_files_in_directory(self, dir_path: str) -> list[str]:
        dir_path = dir_path.rstrip('/')
        return [
            item.path for item in self.repo.tree().traverse()
            if item.path.startswith(dir_path + '/') and item.type == 'blob'
        ]