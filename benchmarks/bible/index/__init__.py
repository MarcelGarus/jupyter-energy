from typing import Iterable, List, Optional, Tuple, Union, NamedTuple, Dict
from abc import ABC, abstractmethod
from pydantic import BaseModel
import logging
import sys

logger = logging.getLogger('BibleCrawler')


class BibelReferenz(BaseModel):
    buch: str
    kapitel: int
    vers: Optional[int]
    bis_vers: Optional[int]


class BibelVers(BaseModel):
    number: int
    text: str
    references: List[BibelReferenz]


class BibelKapitel(BaseModel):
    """
    This is the representation of a "document" in our IR system.

    For more information, check out this resource:
    https://menora-bibel.jimdofree.com/aufbau-der-bibel/
    """
    testament: str
    buch: str
    kapitel: int
    verse: List[BibelVers]

    @property
    def text(self):
        return ' '.join([v.text for v in self.verse])


class TextProcessor(ABC):
    @abstractmethod
    def process_doc(self, src: Union[Iterable[str], str]) -> Iterable[str]:
        raise NotImplementedError("Diese Methode sollte Text, bzw. bereits tokenisierten Text weiter verarbeiten.")


class MemoryFullError(Exception):
    pass


class Posting(NamedTuple):
    document: int
    position: int


class IndexPointer(NamedTuple):
    offset: int
    num_postings: int


class InMemoryIndex(ABC):
    def __init__(self, memory_limit: int = 512):
        self.memory_limit = memory_limit

    def _get_size(self) -> int:
        """
        shamelessly copied from https://goshippo.com/blog/measure-real-size-any-python-object/
        """

        def get_size(obj, seen=None):
            """Recursively finds size of objects"""
            size = sys.getsizeof(obj)
            if seen is None:
                seen = set()
            obj_id = id(obj)
            if obj_id in seen:
                return 0
            # Important mark as seen *before* entering recursion to gracefully handle
            # self-referential objects
            seen.add(obj_id)
            if isinstance(obj, dict):
                size += sum([get_size(v, seen) for v in obj.values()])
                size += sum([get_size(k, seen) for k in obj.keys()])
            elif hasattr(obj, '__dict__'):
                size += get_size(obj.__dict__, seen)
            elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
                size += sum([get_size(i, seen) for i in obj])
            return size

        return get_size(self)

    def _is_full(self):
        return self._get_size() >= self.memory_limit

    def add(self, token: str, posting: Posting):
        self._add(token, posting)
        if self._is_full():
            raise MemoryFullError(f'InMemoryIndex contains more then {self.memory_limit} bytes!')

    @abstractmethod
    def __len__(self):
        """Diese Methode gibt die Anzahl der Einträge im Index zurück"""
        raise NotImplementedError

    @abstractmethod
    def clear(self):
        raise NotImplementedError("Diese Methode soll den in-memory Index komplett leeren.")

    @abstractmethod
    def _add(self, token: str, posting: Posting):
        """
        Diese Methode sollte das gegebene Posting in den temporären Index einfügen.
        Legen Sie sich dafür geeignete Instanzvariablen an um den Index zu speichern.
        Vermeiden Sie wenn möglich `dict()` und arbeiten Sie so platzsparend und
        effizient (CPU) wie möglich.
        """
        raise NotImplementedError("Diese Methode sollte das gegebene Posting in den temporären Index einfügen.")

    @abstractmethod
    def iterate_index(self) -> Iterable[Tuple[str, Iterable[Posting]]]:
        """
        Diese Methode sollte eine alphabetisch sortierte Liste via yield zurückgeben.
        Die Sortierung erfolgt aufsteigend (a-z) nach Token. Pro Token wird ein Tupel
        mit yield zurückgegeben, bestehend aus dem Token selbst und einer Liste an Postings.
        """
        raise NotImplementedError("Diese Methode sollte einen generator für speicherbare Elemente liefern.")


def get_file_size(file):
    file.seek(0, 2)
    return file.tell()


class SearchIndex(ABC):
    def __init__(self, documents: str, index_file: str,
                 temp_index: InMemoryIndex, pre_processing: List[TextProcessor]):
        self.documents_filename = documents
        self.index_filename = index_file
        self.pre_processing_pipeline = pre_processing
        self.temp_index = temp_index

    @abstractmethod
    def get_input_size(self) -> int:
        """
        Return size in bytes of the file `self.documents_filename`
        """
        raise NotImplementedError

    @abstractmethod
    def get_index_size(self) -> int:
        """
        Return size in byte of the index file.
        """
        raise NotImplementedError

    @abstractmethod
    def read_docs(self):
        """
        Dies ist die Haupt-Methode zur Konstruktion des Index.
        Sie iteriert alle Kapitel in der Eingabedatei und baut einen
        positional index. Schauen Sie zur weiten Erläuterung dazu bitte
        auf das Übungsblatt und das Video zum Übungsblatt.
        """
        raise NotImplementedError

    @abstractmethod
    def iterate_postings(self, num_postings, seek: int = None) -> Iterable[Posting]:
        """
        Diese Methode springt an eine Position in der Index Datei und liest ab dort
        `num_postings` viele Postings. Diese werden jeweils mit yield zurück gegeben.

        :param num_postings: Anzahl der Postings die ab seek gelesen werden können
        :param seek: wenn gesetzt, springt die Methode an die Position in der Index Datei
        """
        raise NotImplementedError

    @abstractmethod
    def get_index_lookup(self) -> Dict[str, Tuple[int, int]]:
        """
        Diese Methode gibt ein dict() zurück.
        Die Schlüssel (key) sind die im Index gespeicherten Token.
        Die Werte (value) sind Tupel:
            [0] = Offset in bytes (file.tell()) zum ersten Byte der Posting Liste des Tokens
            [1] = Anzahl der Postings für dieses Token

        Denken Sie daran, dass der Index nicht vollständig in den Hauptspeicher passt.
        Sie dürfen annehmen, dass der LookupIndex in dem Hauptspeicher passt.
        """
        raise NotImplementedError
