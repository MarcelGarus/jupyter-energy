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
from tests.data import get_sample, prep_query_results, bibel_index, DOCUMENTS, PRE_PROCESSING

# https://github.com/okken/pytest-check
init_logging('INFO')
logging.disable(logging.DEBUG)
logger = logging.getLogger('test.4a')


# FIXME remove initial _ so test runs.
def _test_full_scan_query():
    fsqp = FullScanQueryProcessor(documents_filename=DOCUMENTS, pipeline=PRE_PROCESSING)

    query, exp_kapitel, exp_hits = get_sample(0)
    result = fsqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str = prep_query_results(result)
    print(query, len(reality_kapitel_str), len(set(reality_kapitel_str)), len(exp_kapitel))
    with save_assert:
        assert sorted(reality_kapitel_str) == sorted(exp_kapitel)
        assert len(reality_kapitel_str) == len(exp_kapitel)
        assert len(exp_hits) == len(reality_hits)
        eh = set([il for ol in exp_hits for il in ol])
        rh = set([il for ol in reality_hits for il in ol])
        difference = eh.symmetric_difference(rh)
        try:
            assert difference == set()
        except AssertionError as e:
            logger.warning(f'Passt nicht ganz: {difference}')
            if len(difference) >= 4:  # etwas schlupf ist erlaubt...
                assert exp_hits == reality_hits

    query, exp_kapitel, exp_hits = get_sample(1)
    result = fsqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str = prep_query_results(result)
    with save_assert:
        assert sorted(reality_kapitel_str) == sorted(exp_kapitel)
        assert len(reality_kapitel_str) == len(exp_kapitel)
        assert len(exp_hits) == len(reality_hits)
        eh = set([il for ol in exp_hits for il in ol])
        rh = set([il for ol in reality_hits for il in ol])
        difference = eh.symmetric_difference(rh)
        try:
            assert difference == set()
        except AssertionError as e:
            logger.warning(f'Passt nicht ganz: {difference}')
            if len(difference) >= 4:  # etwas schlupf ist erlaubt...
                assert exp_hits == reality_hits

    query, exp_kapitel, exp_hits = get_sample(2)
    result = fsqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str = prep_query_results(result)
    with save_assert:
        assert sorted(reality_kapitel_str) == sorted(exp_kapitel)
        assert len(reality_kapitel_str) == len(exp_kapitel)
        eh = set([il for ol in exp_hits for il in ol])
        rh = set([il for ol in reality_hits for il in ol])
        difference = eh.symmetric_difference(rh)
        try:
            assert difference == set()
        except AssertionError as e:
            logger.warning(f'Passt nicht ganz: {difference}')
            if len(difference) >= 4:  # etwas schlupf ist erlaubt...
                assert exp_hits == reality_hits

    query, exp_kapitel, exp_hits = get_sample(3)
    result = fsqp.query(query)
    reality_hits, reality_kapitel, reality_kapitel_str = prep_query_results(result)
    with save_assert:
        assert sorted(reality_kapitel_str) == sorted(exp_kapitel)
        assert len(reality_kapitel_str) == len(exp_kapitel)
        eh = set([il for ol in exp_hits for il in ol])
        rh = set([il for ol in reality_hits for il in ol])
        difference = eh.symmetric_difference(rh)
        try:
            assert difference == set()
        except AssertionError as e:
            logger.warning(f'Passt nicht ganz: {difference}')
            if len(difference) >= 4:  # etwas schlupf ist erlaubt...
                assert exp_hits == reality_hits
