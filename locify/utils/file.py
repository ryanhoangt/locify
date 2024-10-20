from pathlib import Path

from git import Repo

from locify.utils.path import has_image_extension


class GitRepoUtils:
    def __init__(self, abs_repo_path: str) -> None:
        if not Path(abs_repo_path).is_absolute():
            raise ValueError('The path must be absolute')

        self.repo_path = Path(abs_repo_path)
        try:
            self.repo = Repo(self.repo_path)
        except Exception:
            raise Exception(f'Could not find git repository at {abs_repo_path}')

    def get_all_absolute_tracked_files(self) -> list[str]:
        return [
            str(self.repo_path / item.path)
            for item in self.repo.tree().traverse()
            if item.type == 'blob'
        ]

    def get_all_absolute_staged_files(self) -> list[str]:
        return [
            str(self.repo_path / item.a_path) for item in self.repo.index.diff('HEAD')
        ]

    def get_absolute_tracked_files_in_directory(self, rel_dir_path: str) -> list[str]:
        rel_dir_path = rel_dir_path.rstrip('/')
        return [
            str(self.repo_path / item.path)
            for item in self.repo.tree().traverse()
            if item.path.startswith(rel_dir_path + '/') and item.type == 'blob'
        ]


def read_text(abs_path: str) -> str:
    if has_image_extension(abs_path):
        return ''  # Not support image files yet!

    with open(abs_path, 'r') as f:
        return f.read()
