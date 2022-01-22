from index import TextProcessor, BibelKapitel, BibelReferenz, BibelVers, SearchIndex, Posting, InMemoryIndex, \
    MemoryFullError, IndexPointer
from index.bibel_index import BibelIndex
from query import QueryProcessor, QueryKapitelResult
from typing import Iterable, List, Optional, Tuple, NamedTuple, Union, Dict
import logging
from pydantic.error_wrappers import ValidationError
from log import except2str
import string
import sys
import os
import tempfile
import math
from enum import Enum
import time
from collections import defaultdict, Counter

logger = logging.getLogger('query.index')


class BinaryQueryProcessorMode(Enum):
    # order of query terms: ignore
    # ranking of documents: ignore
    # Korrespondiert mit Aufgabe 4b
    NON_POSITIONAL = 0

    # order of query terms: ignore
    # ranking of documents: based on term frequency
    # Korrespondiert mit Aufgabe 4c, d
    TF_RANKING = 1

    # order of query terms: ignore
    # ranking of documents: based on tf-idf average
    # Korrespondiert mit Aufgabe 4c, d
    TFIDF_RANKING = 2

    # order of query terms: yes
    # ranking of documents: based on tf-idf average
    # Korrespondiert mit aufgabe 4g
    POSITIONAL = 3


class IndexMetadataPointer(NamedTuple):
    # index_offset: ab dieser byte position in der Index-Datei beginnt die Posting Liste
    offset: int
    # num_postings: Anzahl der Postings, die ab der Position gespeichert sind
    # Anmerkung: äquivalent to TF (term frequency)
    num_postings: int
    # in so vielen verschiedenen dokumenten taucht das token auf (document frequency)
    num_documents: int


class BinaryQueryProcessor(QueryProcessor):
    def __init__(self, index: BibelIndex, mode: BinaryQueryProcessorMode, n_droppable: int = None, max_gap: int = 2,
                 simulate_sort=False):
        """
        In dieser Klasse implementieren Sie die nötigen Funktionen für Aufgabe 4b,c,d,g
        Die query() Methode ist schon vorbereitet, je nach `mode` implementieren Sie die entsprechenden
        weiteren Methoden um eine Index-basierte Volltextsuche zu ermöglichen. Bedenken Sie wie
        auch beim letzten Mal, dass alle Operationen möglichst keine Listen im Speicher nutzen,
        da die in einem realen IR System zu groß für den Arbeitsspeicher wären.

        :param index: geladener BibelIndex
        :param mode: Modus
        :param simulate_sort: this will break our memory-safe scheme and sort the result
        :param max_gap: OPTIONAL: für 4g, wenn Lücken im Text zwischen Query Termen erlaubt sein sollen
        :param n_droppable: OPTIONAL: können Sie nutzen um zuzulassen, dass n Token des Queries nicht vorkommen müssen
                           (Musterlösung ignoriert das)
        """
        self.mode = mode
        self.index = index
        self.simulate_sort = simulate_sort
        self.max_gap = max_gap
        self.n_droppable = n_droppable

        logger.debug('Loading lookup table...')
        self.lookup = index.get_index_lookup()

        self.num_docs = 0
        if mode == BinaryQueryProcessorMode.POSITIONAL or mode == BinaryQueryProcessorMode.TFIDF_RANKING:
            logger.debug('Initialising additional meta-data...')
            self.lookup_meta = self._init_metadata()

        logger.debug(f'Loaded index with {len(self.lookup)} words in vocab and {self.num_docs} documents '
                     f'with mode={mode}.')

    def beispiel_index_nutzung(self):
        # Ein Token zu dem wir die Posting-Liste haben wollen
        suchterm = 'klug'

        # offset: ab dieser byte position in der Index-Datei beginnt die Posting Liste
        # num_postings: Anzahl der Postings, die ab der Position gespeichert sind
        index_pointer = self.lookup[suchterm]

        # Ein Iterator an postings. Also keine Liste und es wäre (theoretisch) zu groß mit
        # list(postings) den Iterator als Liste im Speicher zu persistieren.
        postings = self.index.iterate_postings(index_pointer.num_postings, seek=index_pointer.offset)

        last_doc = None
        hits = []
        score = 0.0
        for posting in postings:
            # Ein Posting besteht aus Dokument und Position im Dokument
            print(posting)

            # So kann man ein Kapitel laden
            kapitel = self.index.load_kapitel(posting.document)

            # Zu beachten: posting.position verweist nicht unbedingt
            #              auf das richtige Token in kapitel.text
            # Der richtige Verweis wäre:
            #      self.index.text_processing(kapitel.text)[posting.position]
            # Benötigt man aber nicht für die Aufgaben.
            print(f'Das Token "{suchterm}" kommt in Kapitel '
                  f'"{kapitel.buch} {kapitel.kapitel}" Stelle {posting.position} vor.')

            score += 1
            hits.append((suchterm, posting.position))

            if last_doc is None or last_doc != posting.document:
                yield QueryKapitelResult(hits=hits, kapitel=kapitel, rank_score=score)
                last_doc = posting.document
                hits = []

        # Hinweis: das letzte Kapitel würde hier noch zurückgegeben werden...

    def beispiel_postings_iterieren(self):
        term1 = 'brot'
        term2 = 'tal'

        iteratoren = {}

        index_pointer = self.lookup[term1]
        iteratoren[term1] = self.index.iterate_postings(index_pointer.num_postings, seek=index_pointer.offset)
        index_pointer = self.lookup[term2]
        iteratoren[term2] = self.index.iterate_postings(index_pointer.num_postings, seek=index_pointer.offset)

        print(next(iteratoren[term1]))
        print(next(iteratoren[term1]))
        print(next(iteratoren[term2]))
        print(next(iteratoren[term1]))
        print(next(iteratoren[term2]))
        print(next(iteratoren[term2]))
        print(next(iteratoren[term1]))
        print(next(iteratoren[term2]))
        # irgendwas stimmt doch hier nicht...

        # iterate_postings iteriert auf der index Datei. Angenommen zwei Iteratoren werden abwechselnd
        # iteriert, dann bewegt sich der pointer weiter, aber das Ergebnis macht keinen Sinn.
        # Daher gibt es den conflict_safe modus, der merkt sich bei jedem Schritt für jeden der
        # Iteratoren die Position in der Datei und springt falls nötig hin und her.
        index_pointer = self.lookup[term1]
        iteratoren[term1] = self.index.iterate_postings(index_pointer.num_postings,
                                                        seek=index_pointer.offset, conflict_safe=True)
        index_pointer = self.lookup[term2]
        iteratoren[term2] = self.index.iterate_postings(index_pointer.num_postings,
                                                        seek=index_pointer.offset, conflict_safe=True)

        print(next(iteratoren[term1]))
        print(next(iteratoren[term1]))
        print(next(iteratoren[term2]))
        print(next(iteratoren[term1]))
        print(next(iteratoren[term2]))
        print(next(iteratoren[term2]))
        print(next(iteratoren[term1]))
        print(next(iteratoren[term2]))

    def _init_metadata(self) -> Dict[str, IndexMetadataPointer]:
        """
        Diese Methode iteriert den vorhandenen self.lookup und ersetzt
        alle Einträge (IndexPointer) mit IndexMetadataPointer um so
        angereicherte Informationen zu haben.
        Sie dürfen zur Vereinfachung davon ausgehen, dass die Liste der Document IDs
        in den Hauptspeicher passt.
        """
        metadata_lookup = defaultdict(lambda: IndexMetadataPointer(offset=0, num_postings=0, num_documents=0))
        all_docs = set()
        for term in self.lookup.keys():
            offset, num_postings = self.lookup[term]
            docs_with_t = set(map(lambda posting: posting.document, self.index.iterate_postings(num_postings, seek=offset)))
            metadata_lookup[term] = IndexMetadataPointer(offset=offset, num_postings=num_postings, num_documents=len(docs_with_t))
            all_docs.update(docs_with_t)
        # print(f'all docs are {all_docs}')
        self.num_docs = len(all_docs)
        return metadata_lookup

    def _tf_idf(self, token: str, tf: int):
        """
        Bekommt das Token und die Term Frequency des Tokens im aktuellen Dokument.
        Gibt den TF-IDF Score zurück.
        Hinweise hier: https://en.wikipedia.org/wiki/Tf%E2%80%93idf
        Sie können eine beliebige Variation nutzen.
        Tests nutzen: log(1 + tf(t, d)) * log(N / num docs mit t)

        Nötige Metadaten sollten vorab mit self._init_metadata vorbereitet werden.
        """
        metadata = self.lookup_meta[token]
        if metadata.num_documents == 0:
            # Tokens that don't appear at all get the lowest score, 0.
            return 0
        return math.log(1 + tf) * math.log(self.num_docs / metadata.num_documents)

    def _query_non_positional(self, query: List[str]) -> Iterable[QueryKapitelResult]:
        """
        Gegeben ein bereits geparster Query.
        Nutzen Sie den Index um effizient die Anfrage auszuführen und passende Dokumente zu finden.
        Versuchen Sie zu keinem Zeitpunkt eine Ergebnisliste oder größere Iteratoren im Speicher zu halten.
        In einem web-scale index wäre das auch nicht möglich.

        Tipp: Sie können den Algorithmus von merkeIndexPartitions aus dem Lehrbuch
              clever anpassen und mit ein Mail über die relevanten Postings iterieren
              eine Ergebnisliste erzeugen. Sie müssen nur dort, wo addPostings passiert
              noch prüfen, ob wirklich alle Terme aus der Anfrage dabei sind.
        http://www.ir.uwaterloo.ca/book/04-static-inverted-indices.pdf#page=26
        """
        # Vorgehen: Es gibt mehrere Iteratoren – für jeden Suchbegriff einen. Wir suchen nur
        # Kapitel, in denen alle Terme vorkommen (konjunktiv). Der maximal weite Iterator gibt den
        # nächsten Kapitelkandidaten an (weil es muss ja möglich sein, von jedem Iterator noch zu
        # dem Kapitel zu kommen). Dann advancen wir alle Iteratoren so lange, bis sie entweder auch
        # bei dem Kapitel sind (der jeweilige Suchbegriff existert also auch im Kapitel – ab da
        # können wir die Postings speichern) oder sie haben kein Posting in diesem Kapitel
        # (der jeweilige Suchbegriff existiert in dem Kapitel nicht und wir können das Kapitel als
        # Kandidaten verwerfen).

        # Dictionary von Suchtermen zu Iteratoren.
        iteratoren = {}
        for term in query:
            try:
                index_pointer = self.lookup[term]
                iteratoren[term] = self.index.iterate_postings(index_pointer.num_postings,
                                                        seek=index_pointer.offset, conflict_safe=True)
            except KeyError:
                # Einer der Suchbegriffe existiert nicht mal im Index. Das ist natürlich für den
                # User doof, macht es aber einfach für uns.
                return

        # Wir holen die aktuellen Postings von allen Iteratoren.
        # NOTE: Das kann eleganter ohne Extra-Variable durch peek() gelöst werden, aber dazu müsste
        # man aber entweder selbst ein peekable implementieren, oder ein weiteres externes package
        # nutzen, z.B. more-itertools.
        iteratoren_postings = {}
        for term in query:
            # Dies wirft keine StopIteration, weil Suchbegriffe, die im Index vorkommen, mindestens
            # einen Posting-Eintrag haben.
            iteratoren_postings[term] = next(iteratoren[term])

        abort = False
        while not abort:
            # Das nächste Kapitel muss das maximale von allen Iteratoren sein. Für die anderen
            # existiert mindestens ein Iterator, der bereits weiter ist – also ein Suchbegriff, den
            # es in dem Kapitel nicht gibt.
            kapitel_candidate = max(map(lambda p: p.document, iteratoren_postings.values()))
            found_terms = set()
            hits = []
            for term in query:
                # Zunächst Postings überspringen, bis wir beim gesuchten Kapitel sind.
                while iteratoren_postings[term].document < kapitel_candidate:
                    # Wir haben den Kandidaten noch nicht erreicht.
                    try:
                        iteratoren_postings[term] = next(iteratoren[term])
                    except StopIteration:
                        # Wir haben alle Vorkommnisse dieses Suchbegriffs abgefrühstückt. Das heißt,
                        # es ergibt keinen Sinn, noch weiter nach Kapiteln zu suchen.
                        abort = True
                        break
                if abort:
                    break

                if iteratoren_postings[term].document > kapitel_candidate:
                    # Der Kapitelkandidat wurde übersprungen. Das heißt, den Suchbegriff gibt es gar
                    # nicht in dem Kapitel. Schade. Dann suchen wir uns mal den nächsten Kandidaten
                    # raus!
                    continue

                # Der Iterator ist jetzt bei dem gesuchten Kapitel – es gibt tatsächlich Postings
                # für den Suchterm in diesem Kapitel. Wir suchen jetzt noch weiter, bis wir alle
                # Auftreten des Suchbegriffs gefunden haben.
                found_terms.add(term)
                while iteratoren_postings[term].document == kapitel_candidate:
                    hits.append([term, iteratoren_postings[term].position])
                    try:
                        iteratoren_postings[term] = next(iteratoren[term])
                    except StopIteration:
                        # Dieser Iterator ist fertig. Wir machen erstmal weiter und schauen ob die
                        # anderen Suchbegriffe auch im Kapitel sind. Nach diesem Durchlauf hören wir
                        # dann aber auf.
                        abort = True
                        break

            if len(found_terms) == len(set(query)):
                # print(f'Found {query} in {kapitel_candidate}. hits={hits} (found={found_terms} query={query})')
                yield QueryKapitelResult(hits=hits, kapitel=self.index.load_kapitel(kapitel_candidate))

    def _query_tf_ranked(self, query: List[str]) -> Iterable[QueryKapitelResult]:
        """
        Gleiches wie oben, nur, dass in der QueryKapitelResult auch der rank_score mit ausgefüllt wird.
        Bei dieser Funktion ist der Score die Summe der Term Frequency im Dokument
        (überlappend mit query, einfach, ohne Normalisierung)
        """
        # Vorgehen: s.o.

        # Dictionary von Suchtermen zu Iteratoren.
        iteratoren = {}
        for term in query:
            try:
                index_pointer = self.lookup[term]
                iteratoren[term] = self.index.iterate_postings(index_pointer.num_postings,
                                                        seek=index_pointer.offset, conflict_safe=True)
            except KeyError:
                # Einer der Suchbegriffe existiert nicht mal im Index. Das ist natürlich für den
                # User doof, macht es aber einfach für uns.
                return

        # Wir holen die aktuellen Postings von allen Iteratoren.
        # NOTE: Das kann eleganter ohne Extra-Variable durch peek() gelöst werden, aber dazu müsste
        # man aber entweder selbst ein peekable implementieren, oder ein weiteres externes package
        # nutzen, z.B. more-itertools.
        iteratoren_postings = {}
        for term in query:
            # Dies wirft keine StopIteration, weil Suchbegriffe, die im Index vorkommen, mindestens
            # einen Posting-Eintrag haben.
            iteratoren_postings[term] = next(iteratoren[term])

        abort = False
        while not abort:
            # Das nächste Kapitel muss das maximale von allen Iteratoren sein. Für die anderen
            # existiert mindestens ein Iterator, der bereits weiter ist – also ein Suchbegriff, den
            # es in dem Kapitel nicht gibt.
            kapitel_candidate = max(map(lambda p: p.document, iteratoren_postings.values()))
            found_terms = set()
            hits = []
            for term in query:
                # Zunächst Postings überspringen, bis wir beim gesuchten Kapitel sind.
                while iteratoren_postings[term].document < kapitel_candidate:
                    # Wir haben den Kandidaten noch nicht erreicht.
                    try:
                        iteratoren_postings[term] = next(iteratoren[term])
                    except StopIteration:
                        # Wir haben alle Vorkommnisse dieses Suchbegriffs abgefrühstückt. Das heißt,
                        # es ergibt keinen Sinn, noch weiter nach Kapiteln zu suchen.
                        abort = True
                        break
                if abort:
                    break

                if iteratoren_postings[term].document > kapitel_candidate:
                    # Der Kapitelkandidat wurde übersprungen. Das heißt, den Suchbegriff gibt es gar
                    # nicht in dem Kapitel. Schade. Dann suchen wir uns mal den nächsten Kandidaten
                    # raus!
                    continue

                # Der Iterator ist jetzt bei dem gesuchten Kapitel – es gibt tatsächlich Postings
                # für den Suchterm in diesem Kapitel. Wir suchen jetzt noch weiter, bis wir alle
                # Auftreten des Suchbegriffs gefunden haben.
                found_terms.add(term)
                while iteratoren_postings[term].document == kapitel_candidate:
                    hits.append([term, iteratoren_postings[term].position])
                    try:
                        iteratoren_postings[term] = next(iteratoren[term])
                    except StopIteration:
                        # Dieser Iterator ist fertig. Wir machen erstmal weiter und schauen ob die
                        # anderen Suchbegriffe auch im Kapitel sind. Nach diesem Durchlauf hören wir
                        # dann aber auf.
                        abort = True
                        break

            if len(found_terms) == len(set(query)):
                yield QueryKapitelResult(hits=hits, rank_score=len(hits), kapitel=self.index.load_kapitel(kapitel_candidate))

    def _query_tfidf_ranked(self, query: List[str]) -> Iterable[QueryKapitelResult]:
        """
        Gleiches wie oben, nur, dass in der QueryKapitelResult auch der rank_score mit ausgefüllt wird.
        Bei dieser Funktion ist der Score die Summe der TF-IDF scores
        """
        # Vorgehen: s.o.

        # Dictionary von Suchtermen zu Iteratoren.
        iteratoren = {}
        for term in query:
            try:
                index_pointer = self.lookup[term]
                iteratoren[term] = self.index.iterate_postings(index_pointer.num_postings,
                                                        seek=index_pointer.offset, conflict_safe=True)
            except KeyError:
                # Einer der Suchbegriffe existiert nicht mal im Index. Das ist natürlich für den
                # User doof, macht es aber einfach für uns.
                return

        # Wir holen die aktuellen Postings von allen Iteratoren.
        # NOTE: Das kann eleganter ohne Extra-Variable durch peek() gelöst werden, aber dazu müsste
        # man aber entweder selbst ein peekable implementieren, oder ein weiteres externes package
        # nutzen, z.B. more-itertools.
        iteratoren_postings = {}
        for term in query:
            # Dies wirft keine StopIteration, weil Suchbegriffe, die im Index vorkommen, mindestens
            # einen Posting-Eintrag haben.
            iteratoren_postings[term] = next(iteratoren[term])

        abort = False
        while not abort:
            # Das nächste Kapitel muss das maximale von allen Iteratoren sein. Für die anderen
            # existiert mindestens ein Iterator, der bereits weiter ist – also ein Suchbegriff, den
            # es in dem Kapitel nicht gibt.
            kapitel_candidate = max(map(lambda p: p.document, iteratoren_postings.values()))
            found_terms = set()
            hits = []
            for term in query:
                # Zunächst Postings überspringen, bis wir beim gesuchten Kapitel sind.
                while iteratoren_postings[term].document < kapitel_candidate:
                    # Wir haben den Kandidaten noch nicht erreicht.
                    try:
                        iteratoren_postings[term] = next(iteratoren[term])
                    except StopIteration:
                        # Wir haben alle Vorkommnisse dieses Suchbegriffs abgefrühstückt. Das heißt,
                        # es ergibt keinen Sinn, noch weiter nach Kapiteln zu suchen.
                        abort = True
                        break
                if abort:
                    break

                if iteratoren_postings[term].document > kapitel_candidate:
                    # Der Kapitelkandidat wurde übersprungen. Das heißt, den Suchbegriff gibt es gar
                    # nicht in dem Kapitel. Schade. Dann suchen wir uns mal den nächsten Kandidaten
                    # raus!
                    continue

                # Der Iterator ist jetzt bei dem gesuchten Kapitel – es gibt tatsächlich Postings
                # für den Suchterm in diesem Kapitel. Wir suchen jetzt noch weiter, bis wir alle
                # Auftreten des Suchbegriffs gefunden haben.
                found_terms.add(term)
                while iteratoren_postings[term].document == kapitel_candidate:
                    hits.append([term, iteratoren_postings[term].position])
                    try:
                        iteratoren_postings[term] = next(iteratoren[term])
                    except StopIteration:
                        # Dieser Iterator ist fertig. Wir machen erstmal weiter und schauen ob die
                        # anderen Suchbegriffe auch im Kapitel sind. Nach diesem Durchlauf hören wir
                        # dann aber auf.
                        abort = True
                        break

            if len(found_terms) == len(set(query)):
                score = 0
                for term in query:
                    num_hits = sum(map(lambda hit: 1 if hit[0] == term else 0, hits))
                    score += self._tf_idf(term, num_hits)
                yield QueryKapitelResult(hits=hits, rank_score=score, kapitel=self.index.load_kapitel(kapitel_candidate))

    def _query_positional(self, query: List[str]) -> Iterable[QueryKapitelResult]:
        """
        Gleiches wie tf-idf query mit der Erweiterung, dass die Wortreihenfolge im Query eine Rolle spielt.
        Sie können die entsprechenden Klassenvariablen nutzen um Abstände zwischen den Wörtern zu erlauben oder
        sogar ganze Wörter ausfallen zu lassen. Wortabstand ist zu empfehlen, da ggf. Stoppwörter fehlen.
        """
        raise NotImplementedError

    def query(self, query: str) -> Iterable[QueryKapitelResult]:
        query_terms = list(self.index.text_processing(query))
        # logger.debug(f'Query "{query}" transformed to {query_terms}')

        # oops, nothing left from the query
        if len(query_terms) < 1:
            return

        if self.mode == BinaryQueryProcessorMode.NON_POSITIONAL:
            yield from self._query_non_positional(query_terms)
        elif self.mode == BinaryQueryProcessorMode.TF_RANKING:
            results = self._query_tf_ranked(query_terms)
            if self.simulate_sort:
                # This is not smart at all!
                # This goes against all our efforts to keep everything out of memory.
                # Assume, this never happened and we have a black box that can sort our stuff out-of-memory!
                for r in sorted(list(results),
                                key=lambda r: (r.rank_score, r.kapitel.buch, r.kapitel.kapitel), reverse=True):
                    yield r
            else:
                yield from results
        elif self.mode == BinaryQueryProcessorMode.TFIDF_RANKING:
            results = self._query_tfidf_ranked(query_terms)
            if self.simulate_sort:
                for r in sorted(list(results),
                                key=lambda r: (r.rank_score, r.kapitel.buch, r.kapitel.kapitel), reverse=True):
                    yield r
            else:
                yield from results
        elif self.mode == BinaryQueryProcessorMode.POSITIONAL:
            results = self._query_positional(query_terms)
            if self.simulate_sort:
                for r in sorted(list(results),
                                key=lambda r: (r.rank_score, r.kapitel.buch, r.kapitel.kapitel), reverse=True):
                    yield r
            else:
                yield from results
        else:
            logger.fatal('Nope.')
