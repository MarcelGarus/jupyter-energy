import sys
import os

# myPath = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(1, myPath + '/../')

import re
import time
from copy import deepcopy as copy
from pytest_check import check as save_assert
import pytest_check as check
from typing import Iterable, List, Optional, Tuple, NamedTuple, Union, Dict
from index import BibelKapitel
from index.bibel_engine import SimpleTokenizer, ShortTokenFilter, StopwordFilter, CISTEMStemmer
from index.bibel_index import BibelIndex, InMemoryBibelIndex
from query.naive import FullScanQueryProcessor
from query import QueryProcessor, QueryKapitelResult
from query.index import BinaryQueryProcessor, BinaryQueryProcessorMode
import logging
from log import init_logging, except2str
from tests.data import get_sample, prep_query_results, bibel_index

# https://github.com/okken/pytest-check
init_logging('INFO')
# logging.disable(logging.DEBUG)
logger = logging.getLogger('test.4c')

bqp = BinaryQueryProcessor(index=bibel_index, mode=BinaryQueryProcessorMode.TFIDF_RANKING)


def test_metadata():
    check.equal(bqp.num_docs, 1331, 'Total number of documents')
    check.equal(bqp.lookup_meta['maria'].num_documents, 18, 'Number of documents "Maria" appears in')
    check.equal(bqp.lookup_meta['maria'].num_postings, 50, 'Number of times "Maria" appears')


def test_tfidf():
    check.equal(bqp._tf_idf('maria', 1), 2.982830008098815)
    check.equal(bqp._tf_idf('maria', 5), 7.7105037169612185)
    check.equal(bqp._tf_idf('noah', 5), 7.8129178462050035)
    check.equal(bqp._tf_idf('herr', 5), 0.5650481017580653)
    check.equal(bqp._tf_idf('gott', 5), 0.49804170811335446)
    check.equal(bqp._tf_idf('jesu', 5),  5.553274044117168)
    check.equal(bqp._tf_idf('jesus', 5), 3.3782157717449994)
    check.equal(bqp._tf_idf('jesu', 20), 9.436013996580632)
    check.equal(bqp._tf_idf('jesus', 20), 5.740197773856285)


def test_tfidf_edge_cases():
    # unrealistic cases, but still worth checking
    check.equal(bqp._tf_idf('maria', 50), 16.919880528732758)
    check.equal(bqp._tf_idf('UNKOWN_KEY', 5), 0.0)
