from pathlib import Path

from git import Repo

from locify.utils.path import get_depth_of_rel_path, has_image_extension


class GitRepoUtils:
    def __init__(self, abs_repo_path: str) -> None:
        if not Path(abs_repo_path).is_absolute():
            raise ValueError('The path must be absolute')

        self.repo_path = Path(abs_repo_path)
        try:
            self.repo = Repo(self.repo_path)
        except Exception:
            raise Exception(f'Could not find git repository at {abs_repo_path}')

        # TODO: use BFS to traverse subdirectories to find if there are any git repositories in them

    def get_all_absolute_tracked_files(self, depth: int | None = None) -> list[str]:
        return [
            str(self.repo_path / item.path)
            for item in self.repo.tree().traverse()
            if item.type == 'blob'
            and (not depth or get_depth_of_rel_path(item.path) <= depth)
        ]

    def get_all_absolute_staged_files(self) -> list[str]:
        return [
            str(self.repo_path / item.a_path) for item in self.repo.index.diff('HEAD')
        ]

    def get_absolute_tracked_files_in_directory(
        self, rel_dir_path: str, depth: int | None = None
    ) -> list[str]:
        rel_dir_path = rel_dir_path.rstrip('/')
        return [
            str(self.repo_path / item.path)
            for item in self.repo.tree().traverse()
            if item.path.startswith(rel_dir_path + '/')
            and item.type == 'blob'
            and (not depth or get_depth_of_rel_path(item.path) <= depth)
        ]


def read_text(abs_path: str) -> str:
    if has_image_extension(abs_path):
        return ''  # Not support image files yet!

    with open(abs_path, 'r') as f:
        return f.read()
