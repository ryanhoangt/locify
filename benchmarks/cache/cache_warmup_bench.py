import gc
import statistics
import time
from functools import wraps
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from grep_ast import TreeContext

from locify.indexing.full_map.strategy import FullMapStrategy
from locify.utils.file import read_text


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return end_time - start_time, result

    return wrapper


class WarmupBenchmark:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.strategy_with_cache = FullMapStrategy(root=repo_path)

        # Create a subclass that disables caching
        class NoCacheStrategy(FullMapStrategy):
            def render_tree(self, abs_file: str, rel_file: str, lois: list) -> str:
                # Override to bypass cache
                code = read_text(abs_file) or ''
                if not code.endswith('\n'):
                    code += '\n'

                context = TreeContext(
                    filename=rel_file,
                    code=code,
                    color=False,
                    line_number=True,
                    child_context=False,
                    last_line=False,
                    margin=0,
                    mark_lois=False,
                    loi_pad=0,
                    show_top_of_file_parent_scope=False,
                )

                context.lines_of_interest = set()
                context.add_lines_of_interest(lois)
                context.add_context()
                return context.format()

        self.strategy_no_cache = NoCacheStrategy(root=repo_path)

    @measure_time
    def run_get_map(self, strategy, depth=None):
        return strategy.get_map(depth=depth)

    def benchmark_warmup(
        self,
        num_subsequent_calls: int = 5,
        depths: List[Optional[int]] | None = None,
    ):
        """
        Analyze the first call (cold start) vs subsequent calls (warm cache)
        """
        depths = [None, 1, 2, 3] if depths is None else depths
        results = {
            'with_cache': {
                depth: {'first_call': 0, 'subsequent_calls': []} for depth in depths
            },
            'no_cache': {
                depth: {'first_call': 0, 'subsequent_calls': []} for depth in depths
            },
        }

        for depth in depths:
            depth_str = 'Full' if depth is None else f'Depth {depth}'
            print(f'\nBenchmarking {depth_str}:')

            # Test with cache
            print('Testing with cache...')
            self.strategy_with_cache.file_context_cache.clear()
            self.strategy_with_cache.rendered_tree_cache.clear()
            gc.collect()

            # First call
            first_time, _ = self.run_get_map(self.strategy_with_cache, depth)
            results['with_cache'][depth]['first_call'] = first_time

            # Subsequent calls
            for i in range(num_subsequent_calls):
                time_taken, _ = self.run_get_map(self.strategy_with_cache, depth)
                results['with_cache'][depth]['subsequent_calls'].append(time_taken)

            # Test without cache
            print('Testing without cache...')
            gc.collect()

            # First call
            first_time, _ = self.run_get_map(self.strategy_no_cache, depth)
            results['no_cache'][depth]['first_call'] = first_time

            # Subsequent calls
            for i in range(num_subsequent_calls):
                time_taken, _ = self.run_get_map(self.strategy_no_cache, depth)
                results['no_cache'][depth]['subsequent_calls'].append(time_taken)

        return results

    def plot_results(self, results, num_subsequent_calls: int):
        """
        Create visualizations to show the performance differences
        """
        depths = list(results['with_cache'].keys())
        depth_labels = ['Full' if d is None else str(d) for d in depths]

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

        # First subplot: Bar chart for first calls
        first_calls_cache = [results['with_cache'][d]['first_call'] for d in depths]
        first_calls_no_cache = [results['no_cache'][d]['first_call'] for d in depths]

        x = np.arange(len(depths))
        width = 0.35

        ax1.bar(x - width / 2, first_calls_cache, width, label='With Cache')
        ax1.bar(x + width / 2, first_calls_no_cache, width, label='No Cache')

        ax1.set_ylabel('Time (seconds)')
        ax1.set_title('First Call Performance (Cold Start)')
        ax1.set_xticks(x)
        ax1.set_xticklabels(depth_labels)
        ax1.legend()

        # Add improvement percentages
        for i in range(len(depths)):
            improvement = (
                (first_calls_no_cache[i] - first_calls_cache[i])
                / first_calls_no_cache[i]
                * 100
            )
            ax1.text(
                i,
                max(first_calls_cache[i], first_calls_no_cache[i]),
                f'{improvement:.1f}%\nimprovement',
                ha='center',
                va='bottom',
            )

        # Second subplot: Box plot for subsequent calls
        subsequent_data = []
        for depth in depths:
            subsequent_data.extend(
                [
                    (depth_labels[depths.index(depth)], 'With Cache', t)
                    for t in results['with_cache'][depth]['subsequent_calls']
                ]
            )
            subsequent_data.extend(
                [
                    (depth_labels[depths.index(depth)], 'No Cache', t)
                    for t in results['no_cache'][depth]['subsequent_calls']
                ]
            )

        df = pd.DataFrame(subsequent_data, columns=['Depth', 'Type', 'Time'])
        sns.boxplot(data=df, x='Depth', y='Time', hue='Type', ax=ax2)

        ax2.set_ylabel('Time (seconds)')
        ax2.set_title(f'Subsequent Calls Performance ({num_subsequent_calls} calls)')

        # Add median improvement percentages
        for depth in depth_labels:
            cache_median = df[(df['Depth'] == depth) & (df['Type'] == 'With Cache')][
                'Time'
            ].median()
            no_cache_median = df[(df['Depth'] == depth) & (df['Type'] == 'No Cache')][
                'Time'
            ].median()
            improvement = (no_cache_median - cache_median) / no_cache_median * 100
            ax2.text(
                depth_labels.index(depth),
                max(cache_median, no_cache_median),
                f'{improvement:.1f}%\nimprovement',
                ha='center',
                va='bottom',
            )

        plt.tight_layout()
        plt.savefig('cache_warmup_analysis.png')
        plt.close()

        # Print detailed statistics
        print('\nDetailed Statistics:')
        for depth in depths:
            depth_str = 'Full' if depth is None else f'Depth {depth}'
            print(f'\n{depth_str}:')

            # First call stats
            print('\nFirst Call:')
            cache_first = results['with_cache'][depth]['first_call']
            no_cache_first = results['no_cache'][depth]['first_call']
            improvement = (no_cache_first - cache_first) / no_cache_first * 100
            print(f'With Cache:    {cache_first:.3f}s')
            print(f'Without Cache: {no_cache_first:.3f}s')
            print(f'Improvement:   {improvement:.1f}%')

            # Subsequent calls stats
            print('\nSubsequent Calls:')
            cache_subsequent = results['with_cache'][depth]['subsequent_calls']
            no_cache_subsequent = results['no_cache'][depth]['subsequent_calls']

            cache_mean = statistics.mean(cache_subsequent)
            no_cache_mean = statistics.mean(no_cache_subsequent)
            improvement = (no_cache_mean - cache_mean) / no_cache_mean * 100

            print(
                f'With Cache    - Mean: {cache_mean:.3f}s, '
                f'Std: {statistics.stdev(cache_subsequent):.3f}s'
            )
            print(
                f'Without Cache - Mean: {no_cache_mean:.3f}s, '
                f'Std: {statistics.stdev(no_cache_subsequent):.3f}s'
            )
            print(f'Average Improvement: {improvement:.1f}%')


def main():
    # Initialize benchmark
    benchmark = WarmupBenchmark('/home/ryan/numpy')

    # Run warmup analysis
    num_subsequent_calls = 5
    results = benchmark.benchmark_warmup(num_subsequent_calls=num_subsequent_calls)

    # Plot and analyze results
    benchmark.plot_results(results, num_subsequent_calls)


if __name__ == '__main__':
    main()
