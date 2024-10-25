import gc
import statistics
import time
from functools import wraps

import matplotlib.pyplot as plt
import numpy as np
from grep_ast import TreeContext
from memory_profiler import profile

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


class CacheBenchmark:
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

    def benchmark_multiple_runs(self, num_runs=5, depths=None):
        depths = [1, 2, 3] if depths is None else depths
        results = {
            'with_cache': {depth: [] for depth in depths},
            'no_cache': {depth: [] for depth in depths},
        }

        for depth in depths:
            print(f'\nBenchmarking depth {depth}:')

            for run in range(num_runs):
                print(f'Run {run + 1}/{num_runs}')

                # Clear caches between runs
                self.strategy_with_cache.file_context_cache.clear()
                self.strategy_with_cache.rendered_tree_cache.clear()
                gc.collect()

                # Measure with cache
                time_with_cache, _ = self.run_get_map(self.strategy_with_cache, depth)
                results['with_cache'][depth].append(time_with_cache)

                # Measure without cache
                time_no_cache, _ = self.run_get_map(self.strategy_no_cache, depth)
                results['no_cache'][depth].append(time_no_cache)

                # Force garbage collection between runs
                gc.collect()

        return results

    @profile
    def profile_memory_usage(self, depth=2):
        """Profile memory usage for a single run"""
        # With cache
        _ = self.strategy_with_cache.get_map(depth=depth)

        # Clear and measure without cache
        gc.collect()
        _ = self.strategy_no_cache.get_map(depth=depth)

    def plot_results(self, results):
        depths = list(results['with_cache'].keys())

        # Calculate means and standard deviations
        means_cache = [statistics.mean(results['with_cache'][d]) for d in depths]
        means_no_cache = [statistics.mean(results['no_cache'][d]) for d in depths]
        stds_cache = [statistics.stdev(results['with_cache'][d]) for d in depths]
        stds_no_cache = [statistics.stdev(results['no_cache'][d]) for d in depths]

        # Create the plot
        plt.figure(figsize=(12, 6))
        x = np.arange(len(depths))
        width = 0.35

        plt.bar(
            x - width / 2,
            means_cache,
            width,
            label='With Cache',
            yerr=stds_cache,
            capsize=5,
        )
        plt.bar(
            x + width / 2,
            means_no_cache,
            width,
            label='No Cache',
            yerr=stds_no_cache,
            capsize=5,
        )

        plt.xlabel('Directory Depth')
        plt.ylabel('Time (seconds)')
        plt.title('Performance Comparison over numpy repo: Cached vs Non-Cached')

        # Format x-axis labels to show "Full" for None and numbers for specific depths
        x_labels = ['Full' if d is None else str(d) for d in depths]
        plt.xticks(x, x_labels)
        plt.legend()

        # Add performance improvement percentages
        for i in range(len(depths)):
            improvement = (
                (means_no_cache[i] - means_cache[i]) / means_no_cache[i]
            ) * 100
            plt.text(
                i,
                max(means_cache[i], means_no_cache[i]),
                f'{improvement:.1f}%\nimprovement',
                ha='center',
                va='bottom',
            )

        plt.tight_layout()
        plt.savefig('cache_benchmark_results_will_full_depth.png')
        plt.close()


def main():
    # Initialize benchmark
    benchmark = CacheBenchmark('/home/ryan/numpy')

    # Run benchmarks with multiple depths, including None for full repository
    depths = [None, 1, 2, 3]  # None represents full repository depth
    results = benchmark.benchmark_multiple_runs(num_runs=5, depths=depths)

    # Plot results
    benchmark.plot_results(results)

    # Profile memory usage
    print('\nProfiling memory usage...')
    benchmark.profile_memory_usage(depth=2)

    # Print detailed statistics
    print('\nDetailed Statistics:')
    for depth in depths:
        cache_times = results['with_cache'][depth]
        no_cache_times = results['no_cache'][depth]

        print(f'\nDepth {depth}:')
        print(
            f'With Cache    - Mean: {statistics.mean(cache_times):.3f}s, '
            f'Std: {statistics.stdev(cache_times):.3f}s'
        )
        print(
            f'Without Cache - Mean: {statistics.mean(no_cache_times):.3f}s, '
            f'Std: {statistics.stdev(no_cache_times):.3f}s'
        )

        improvement = (
            (statistics.mean(no_cache_times) - statistics.mean(cache_times))
            / statistics.mean(no_cache_times)
            * 100
        )
        print(f'Performance Improvement: {improvement:.1f}%')


if __name__ == '__main__':
    main()
    main()
