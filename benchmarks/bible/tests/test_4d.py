import sys
import os
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
logger = logging.getLogger('test.4b')


def test_index_query_mode_tf_ranking():
    bqp = BinaryQueryProcessor(index=bibel_index, mode=BinaryQueryProcessorMode.TF_RANKING)

    query, exp_kapitel, exp_hits = get_sample(4)
    result = bqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str, scores = prep_query_results(result, sort=True)
    with save_assert:
        assert reality_kapitel_str == exp_kapitel

    query, exp_kapitel, exp_hits = get_sample(5)
    result = bqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str, scores = prep_query_results(result, sort=True)
    with save_assert:
        assert reality_kapitel_str == exp_kapitel

    query, exp_kapitel, exp_hits = get_sample(6)
    result = bqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str, scores = prep_query_results(result, sort=True)
    with save_assert:
        assert reality_kapitel_str == exp_kapitel


def test_index_query_mode_tfidf_ranking():
    bqp = BinaryQueryProcessor(index=bibel_index, mode=BinaryQueryProcessorMode.TFIDF_RANKING)

    query, exp_kapitel, exp_hits = get_sample(7)
    result = bqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str, scores = prep_query_results(result, sort=True)
    with save_assert:
        assert reality_kapitel_str == exp_kapitel

    query, exp_kapitel, exp_hits = get_sample(8)
    result = bqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str, scores = prep_query_results(result, sort=True)
    with save_assert:
        assert reality_kapitel_str == exp_kapitel

    query, exp_kapitel, exp_hits = get_sample(9)
    result = bqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str, scores = prep_query_results(result, sort=True)
    with save_assert:
        assert reality_kapitel_str == exp_kapitel
