from abc import ABC, abstractmethod
from typing import Iterable, List, Tuple, Optional
from index import BibelKapitel, TextProcessor
from pydantic import BaseModel


class QueryKapitelResult(BaseModel):
    hits: List[Tuple[str, int]]
    rank_score: Optional[float] = 1.0
    kapitel: BibelKapitel

    def as_reference(self) -> str:
        return f'{self.kapitel.buch} {self.kapitel.kapitel}'

    def as_snippet(self) -> Tuple[str, str]:
        """
        Given a query result, return title and text snippet
        """
        window_size = 10
        centre_hit = self.hits[0]

        # We get the raw text here, however, the index works on tokenised, stemmed text
        # with stopwords and short tokens removed. So we start where the positing was in
        # the processed text and search forward till we (hopefully) find what we actually
        # want. This is not ideal, but a good enough heuristic.
        token_heuristic = self.kapitel.text.lower().split()
        for i in range(centre_hit[1], len(token_heuristic)):
            # if i < centre_hit[1]+2:
            if centre_hit[0].lower() in token_heuristic[i].lower():
                return self.as_reference(), ' '.join(token_heuristic[max(0, i - window_size):
                                                                     min(i + window_size, len(token_heuristic))])
        # Apparently the heuristic didn't work out, pretend the word is at the original position
        return self.as_reference(), ' '.join(token_heuristic[max(0, centre_hit[1] - window_size):
                                                             min(centre_hit[1] + window_size,
                                                                 len(token_heuristic))])


class QueryProcessor(ABC):

    @classmethod
    def to_reference_list(cls, results: Iterable[QueryKapitelResult]) -> Iterable[str]:
        for result in results:
            yield result.as_reference()

    @classmethod
    def to_text_result_list(cls, results: Iterable[QueryKapitelResult]) -> Iterable[str]:
        for result in results:
            yield result.as_snippet()

    @abstractmethod
    def query(self, query: str) -> Iterable[QueryKapitelResult]:
        """
        This method parses the query string and queries the index accordingly.
        It returns a tuple with the number of documents found and an iterable
        of documents (in this case bible chapters, that are yielded one by one).
        """
        raise NotImplementedError
