import argparse
import logging
import time

from index.bibel_engine import (CISTEMStemmer, CustomStemmer, PorterStemmer,
                                ShortTokenFilter, SimpleTokenizer,
                                StopwordFilter)
from index.bibel_index import BibelIndex, InMemoryBibelIndex
from log import except2str, init_logging
from query import QueryProcessor
from query.index import BinaryQueryProcessor, BinaryQueryProcessorMode
from query.naive import FullScanQueryProcessor

parser = argparse.ArgumentParser(description='Der Bibel Suchindex')
parser.add_argument('--docs', type=str, default='results.json',
                    help='File with the previously crawled data.')
parser.add_argument('--index', type=str, default='inverted_index.bin',
                    help='Target file to store inverted index in')
parser.add_argument('--stemmer', type=str, default='porter', choices=['porter', 'cistem', 'custom'],
                    help='Stemmer to use')
parser.add_argument('--index-stats', action='store_true',
                    help='Set this flag to list some stats of an existing index')
parser.add_argument('--build-index', action='store_true',
                    help='Set this flag to rebuild the index from docs.')
parser.add_argument('--memory-limit', type=int, default=100 * 1024,
                    help='Maximum capacity in bytes of the temporary in-memory index')
parser.add_argument('--speed-comparison', action='store_true',
                    help='Set this flag to run a speed comparison between a full scan and with indexed data')
parser.add_argument('--interactive', action='store_true',
                    help='Set this flag to get an interactive search console')
parser.add_argument('--log', type=str, default='DEBUG',
                    choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
                    help='Log Level')
args = parser.parse_args()

init_logging(args.log)
logger = logging.getLogger('main')

logger.debug('debug')
logger.info('info')
logger.warning('warn')
logger.error('error')
logger.fatal('fatal')

if args.stemmer == 'custom':
    bibel_stemmer = CustomStemmer()
elif args.stemmer == 'cistem':
    bibel_stemmer = CISTEMStemmer()
else:
    bibel_stemmer = PorterStemmer()

PRE_PROCESSING = [
    SimpleTokenizer(),
    ShortTokenFilter(min_len=2),
    StopwordFilter(stopword_file='stopwords.txt'),
    bibel_stemmer
]

temporary_index = InMemoryBibelIndex(memory_limit=args.memory_limit)
bibel_index = BibelIndex(documents=args.docs,
                         pre_processing=PRE_PROCESSING,
                         temp_index=temporary_index,
                         index_file=args.index)

if args.build_index:
    logger.info('Initialised BibelIndex, reading chapters...')
    bibel_index.read_docs()

if args.index_stats:
    lookup = bibel_index.get_index_lookup()
    logger.info('== BibelIndex Stats ==')

    most_popular = sorted(lookup.items(), key=lambda l: l[1][1], reverse=True)

    logger.info('~~ most popular tokens ~~')
    for token, (offset, tf) in most_popular[:20]:
        logger.info(f'"{token}" appeared {tf} times, posting starts at '
                    f'{(offset / bibel_index.get_index_size() * 100):.2f}% of the file')

    logger.info('~~ least popular tokens ~~')
    for token, (offset, tf) in reversed(most_popular[-20:]):
        logger.info(f'"{token}" appeared {tf} times, posting starts at '
                    f'{(offset / bibel_index.get_index_size() * 100):.2f}% of the file')

    logger.info(f'Number of distinct tokens: {len(lookup)}')
    logger.info(f'Index Size: {(bibel_index.get_index_size() / 1024):.2f}KB')
    logger.info(f'Bible Size: {(bibel_index.get_input_size() / 1024):.2f}KB')

if args.interactive:
    EXIT_KEYWORD = 'quit()'

    logger.info('*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*')
    logger.info(f'Welcome to the interactive search console.')
    logger.info(f'Type "{EXIT_KEYWORD}" to quit the program.')
    logger.info('')
    logger.info('Which QueryProcessor would you like to use?')
    logger.info('> [1] FullScanQueryProcessor')
    logger.info('> [2] BinaryQueryProcessor (mode=NON_POSITIONAL)')
    processor = input('Enter the number: ')

    if processor == '1':
        query_processor = BinaryQueryProcessor(bibel_index, mode=BinaryQueryProcessorMode.NON_POSITIONAL)
    elif processor == '2':
        query_processor = FullScanQueryProcessor(documents_filename=args.docs, pipeline=PRE_PROCESSING)
    else:
        logger.error(f'Invalid option "{processor}"!')
        raise ReferenceError

    while True:
        query = input('Enter your search query: ')
        if query == EXIT_KEYWORD:
            logger.info('Exiting interactive search console.')
            break
        results = query_processor.query(query)
        cnt = 0
        for result in results:
            title, snippet = result.as_snippet()
            if cnt < 5:
                logger.info(f' ~~ {title} ~~')
                logger.info(f'[..] {snippet} [..]')
            cnt += 1
        logger.info(f'This query matched to {cnt} bible chapters.')

elif args.speed_comparison:
    example_queries = [
        'Jesus', 'der Himmel', 'es stand geschrieben', 'Maria', 'herr', 'gott',
        'herr gott', 'moses', 'gott', 'jesus', 'engel', 'gabriel', 'johannes',
        'täufer', 'frucht', 'baum', 'meer', 'fisch', 'zimt', 'esel', 'abkomme'
    ]

    logging.disable(logging.DEBUG)


    def test(processor: QueryProcessor):
        global_start_time = time.time()
        for i, query in enumerate(example_queries):
            start_time = time.time()
            docs = []
            try:
                for result in processor.query(query):
                    docs.append(result.as_reference())
                    # logger.debug(f'{len(hits)} hits ({Counter([h[0] for h in hits])}) '
                    #              f'in {kapitel.buch} {kapitel.kapitel}')
            except Exception as e:
                # logger.error(except2str(e))
                except2str(e, logger)
            used_time = time.time() - start_time
            logger.info(f'{i}) "{query}" took {used_time:.3f}s and found {len(docs)}')
            # logger.debug(f'{docs}')
        logger.info(f'All queries took {(time.time() - global_start_time):.3f}s')


    logger.info('')
    logger.info('~~ Testing Index Queries (mode: NON_POSITIONAL) ~~')
    test(BinaryQueryProcessor(index=bibel_index, mode=BinaryQueryProcessorMode.NON_POSITIONAL))
    logger.info('')
    logger.info('~~ Testing Index Queries (mode: TF-IDF) ~~')
    test(BinaryQueryProcessor(index=bibel_index, mode=BinaryQueryProcessorMode.TFIDF_RANKING, simulate_sort=True))
    logger.info('')
    # logger.info('~~ Testing Index Queries (mode: POSITIONAL) ~~')
    # test(BinaryQueryProcessor(index=bibel_index, mode=BinaryQueryProcessorMode.POSITIONAL))
    # logger.info('')
    logger.info('~~ Testing Naïve Queries ~~')
    test(FullScanQueryProcessor(documents_filename=args.docs, pipeline=PRE_PROCESSING))

else:
    # query_processor = FullScanQueryProcessor(documents_filename=args.docs, pipeline=PRE_PROCESSING)
    query_processor = BinaryQueryProcessor(bibel_index, mode=BinaryQueryProcessorMode.NON_POSITIONAL)
    # query_processor = BinaryQueryProcessor(bibel_index, mode=BinaryQueryProcessorMode.TF_RANKING, simulate_sort=True)
    # query_processor = BinaryQueryProcessor(bibel_index, mode=BinaryQueryProcessorMode.TFIDF_RANKING, simulate_sort=True)
    results = query_processor.query('maria die jungfrau')

    # # words = ['gott', 'jesus', 'engel', 'gabriel', 'johannes', 'täufer', 'frucht', 'baum', 'meer', 'fisch', 'zimt', 'esel', 'abkomme']
    # words = list(map(lambda i: i[0], bibel_index.get_index_lookup().items()))
    # print(f'Got {len(words)} ready')

    # for query_length in range(1, 21):
    #     benchmarks = []
    #     result_sizes = []
    #     for n in range(100):
    #         # Choose a random query.
    #         query = []
    #         while len(query) < query_length:
    #             query.append(random.choice(words))
    #         query = ' '.join(query)
    #         # Do the search.
    #         start_time = time.time()
    #         results = list(query_processor.query(query))
    #         used_time = time.time() - start_time
    #         benchmarks.append(used_time)
    #         result_sizes.append(len(results))
    #     # Average.
    #     benchmark = sum(benchmarks) / len(benchmarks)
    #     result_size = sum(result_sizes) / len(result_sizes)
    #     print(f'{query_length},{round(benchmark*1000)},{result_size}')

    cnt = 0
    for result in results:
        title, snippet = result.as_snippet()
        if cnt < 5:
            logger.info(f' ~~ {title} ~~')
            logger.info(f'[..] {snippet} [..]')
        cnt += 1
    logger.info(f'This query matched to {cnt} bible chapters.')
