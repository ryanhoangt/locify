import fire
import fire.core

from locify import DirectRefStrategy, FullMapStrategy, RepoMapStrategy


def main(strategy: str, **kwargs):
    valid_strategies = {'fullmap', 'repomap', 'directref'}

    if strategy not in valid_strategies:
        raise fire.core.FireError(
            f"Invalid strategy: {strategy}. Available strategies are: {', '.join(repr(s) for s in valid_strategies)}"
        )

    if strategy == 'fullmap':
        return FullMapStrategy(show_progress=True, **kwargs)
    elif strategy == 'repomap':
        return RepoMapStrategy(show_progress=True, **kwargs)
    else:
        return DirectRefStrategy(show_progress=True, **kwargs)


if __name__ == '__main__':
    fire.Fire(main)
