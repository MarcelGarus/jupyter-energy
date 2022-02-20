import json
import statistics

import colorama


def stats_for_series(series):
    median = statistics.median(series)
    stdev = statistics.stdev(series)
    return (median, stdev)

def pretty_stats(stats):
    return f'{stats[0]:8.2f} stdev {stats[1]:5.2f}'

def print_stats(benchmark, name, path1, path2):
    series_with_extension = list(map(lambda m: m[path1][path2], benchmark['withExtension']))
    stats_with_extension = stats_for_series(series_with_extension)
    output = pretty_stats(stats_with_extension)

    try:
        series_without_extension = list(map(lambda m: m[path1][path2], benchmark['withoutExtension']))
        stats_without_extension = stats_for_series(series_without_extension)
        output += f'  vs. {pretty_stats(stats_without_extension)}'
        additional = stats_with_extension[0] / stats_without_extension[0] - 1
        output += f'  (extension adds {additional * 100:.2f}%)'
    except:
        output += f'                         -'
        pass

    print(f'{name:24} {output}')


def print_stats_for_benchmark(benchmarks, name):
    print('')
    print(f'{colorama.Fore.YELLOW}{name:24}       with extension         without extension{colorama.Style.RESET_ALL}')
    benchmark = benchmarks[name]
    print_stats(benchmark, 'energy internal (RAPL)', 'internal', 'all')
    print_stats(benchmark, '  cpu', 'internal', 'cpu')
    print_stats(benchmark, '  ram', 'internal', 'ram')
    print_stats(benchmark, '  gpu', 'internal', 'gpu')
    print_stats(benchmark, 'energy external (MCP)', 'external', 'mcp0ch2')
    print_stats(benchmark, 'time wall', 'time', 'wall')
    print_stats(benchmark, 'time user', 'time', 'user')

file = open('measurements.json')
data = json.load(file)
file.close()

print_stats_for_benchmark(data, 'kmeans')
print_stats_for_benchmark(data, 'blas/lapack')
print_stats_for_benchmark(data, 'bible')
print_stats_for_benchmark(data, 'idle')
