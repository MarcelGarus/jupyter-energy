from index import TextProcessor, BibelKapitel
from query import QueryProcessor, QueryKapitelResult
from typing import Iterable, List, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger('query.naive')


class FullScanQueryProcessor(QueryProcessor):
    def __init__(self, documents_filename: str, pipeline: List[TextProcessor]):
        self.documents_filename = documents_filename
        self.pipeline = pipeline

    def _kapitel_iter(self) -> Iterable[BibelKapitel]:
        with open(self.documents_filename, 'r') as f:
            for line in f:
                yield BibelKapitel.parse_raw(line)

    def _tokenise(self, text: str) -> Iterable[str]:
        for processor in self.pipeline:
            text = processor.process_doc(text)
        yield from text

    def query(self, query: str) -> Iterable[QueryKapitelResult]:
        """
        Bekommt einen Query String und gibt die BibelKapitel zurück, in denen alle
        Token gefunden wurden. Das Tuple[str, int] sind die einzelnen Treffer im Dokument,
        bestehend aus dem entsprechenden Query-Token und der Stelle im Dokument (BibelKapitel.text).
        Nutzen Sie keine in Python eingebaute string Suche (etwa 'needle' in 'heystack with neelde').

        In Kapitel 10 aus "Information Retrieval: Data Structures & Algorithms"
        gibt es einige Algorithmen zur String Suche ohne Index. Es genügt vollkommen, wenn
        Sie eine einfache Brute-force Suche implementieren:
        for each kapitel:
          for each token in kapitel:
            for each query_token:
              if token == query_token: merken
          liste gemerkter token == liste query_token: kapitel passt auf query.
        https://cdn.preterhuman.net/texts/math/Data_Structure_And_Algorithms/Information%20Retrieval%20Data%20Structures%20&%20Algorithms%20-%20William%20B.%20Frakes.pdf#page=293&zoom=100,0,0
        """
        query_tokens = set(self._tokenise(query))
        for kapitel in self._kapitel_iter():
            hits: List[Tuple[str, int]] = []
            found_query_tokens = set()
            for pos, token in enumerate(self._tokenise(kapitel.text)):
                for query_token in query_tokens:
                    if token == query_token:
                        hits.append((token, pos))
                        found_query_tokens.add(token)
            if  found_query_tokens == query_tokens:
                yield QueryKapitelResult(hits=hits, kapitel=kapitel)
