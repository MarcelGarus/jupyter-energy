import sys
import os
import re
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, myPath + '/../')
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

lookup = bibel_index.get_index_lookup()


def test_index_maria():
    TOKEN = 'maria'

    index_pointer = lookup[TOKEN]
    check.equal(index_pointer.num_postings, 50)
    kapitels = set()
    for posting in bibel_index.iterate_postings(index_pointer.num_postings, seek=index_pointer.offset):
        kapitel = bibel_index.load_kapitel(posting.document)
        kapitels.add(f'{kapitel.buch} {kapitel.kapitel}')
        tokens = list(bibel_index.text_processing(kapitel.text))
        assert tokens[posting.position] == TOKEN
    assert sorted(list(kapitels)) == sorted(['Johannes 19',
                                             'Römer 16',
                                             'Lukas 10',
                                             'Lukas 2',
                                             'Markus 15',
                                             'Matthäus 13',
                                             'Matthäus 28',
                                             'Johannes 11',
                                             'Johannes 20',
                                             'Matthäus 2',
                                             'Lukas 8',
                                             'Lukas 24',
                                             'Johannes 12',
                                             'Markus 16',
                                             'Apostelgeschichte 1',
                                             'Matthäus 1',
                                             'Matthäus 27',
                                             'Lukas 1'])


def test_index_jungfrau():
    TOKEN = 'jungfrau'
    index_pointer = lookup[TOKEN]
    check.equal(index_pointer.num_postings, 83)
    kapitels = set()
    for posting in bibel_index.iterate_postings(index_pointer.num_postings, seek=index_pointer.offset):
        kapitel = bibel_index.load_kapitel(posting.document)
        kapitels.add(f'{kapitel.buch} {kapitel.kapitel}')
        tokens = list(bibel_index.text_processing(kapitel.text))
        assert tokens[posting.position] == TOKEN
    assert sorted(list(kapitels)) == sorted(['1. Korinther 7',
                                             '1. Könige 1',
                                             '2. Chronik 36',
                                             '2. Korinther 11',
                                             '2. Könige 19',
                                             '2. Makkabäer 3',
                                             '2. Makkabäer 5',
                                             '2. Samuel 13',
                                             'Amos 5',
                                             'Amos 8',
                                             'Apostelgeschichte 21',
                                             'Deuteronomium/5. Mose 22',
                                             'Ester 2',
                                             'Exodus/2. Mose 22',
                                             'Ezechiel/Hesekiel 44',
                                             'Ezechiel/Hesekiel 9',
                                             'Genesis/1. Mose 24',
                                             'Hoheslied 6',
                                             'Ijob/Hiob 31',
                                             'Jeremia 14',
                                             'Jeremia 18',
                                             'Jeremia 2',
                                             'Jeremia 31',
                                             'Jeremia 46',
                                             'Jeremia 51',
                                             'Jesaja 23',
                                             'Jesaja 37',
                                             'Jesaja 47',
                                             'Jesaja 62',
                                             'Jesaja 7',
                                             'Joel 1',
                                             'Judit 16',
                                             'Judit 9',
                                             'Klagelieder 1',
                                             'Klagelieder 2',
                                             'Klagelieder 5',
                                             'Levitikus/3. Mose 21',
                                             'Lukas 1',
                                             'Matthäus 1',
                                             'Matthäus 25',
                                             'Nahum 2',
                                             'Psalter 148',
                                             'Psalter 45',
                                             'Psalter 78',
                                             'Richter 19',
                                             'Richter 21',
                                             'Sacharja 9',
                                             'Sirach 20',
                                             'Sirach 30',
                                             'Sirach 42',
                                             'Sirach 9'])
