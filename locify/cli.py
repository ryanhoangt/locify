import fire
import fire.core

from locify import FullMapStrategy, RepoMapStrategy


def main(strategy: str, **kwargs):
    valid_strategies = {'fullmap', 'repomap'}

    if strategy not in valid_strategies:
        raise fire.core.FireError(
            f"Invalid strategy: {strategy}. Available strategies are: {', '.join(repr(s) for s in valid_strategies)}"
        )

    if strategy == 'fullmap':
        return FullMapStrategy(**kwargs)
    else:  # strategy == 'repomap'
        return RepoMapStrategy(**kwargs)


if __name__ == '__main__':
    fire.Fire(main)
