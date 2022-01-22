from index import BibelKapitel, SearchIndex, Posting, InMemoryIndex, MemoryFullError, IndexPointer
from typing import Iterable, Tuple, Union, Dict
from collections import defaultdict
import logging
import sys
import os
import time

logger = logging.getLogger('bibel.index')


class InMemoryBibelIndex(InMemoryIndex):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage = None
        self.init_storage()

    def __len__(self):
        return len(self.storage)

    def init_storage(self):
        self.storage = defaultdict(list)

    def _add(self, token: str, posting: Posting):
        self.storage[token].append(posting)

    def clear(self):
        old_size = self._get_size()

        del self.storage
        self.init_storage()

        logger.debug(f'Cleared in-memory index, size before: {old_size} and after: {self._get_size()}')

    def iterate_index(self) -> Iterable[Tuple[str, int, Iterable[Posting]]]:
        # print(self.storage)
        keys = sorted(self.storage.keys())
        for token in keys:
            yield token, len(self.storage[token]), iter(self.storage[token])


class BibelIndex(SearchIndex):
    DELIMITER = b'#'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bibel_file = open(self.documents_filename, 'rb')
        self.index_file = open(self.index_filename, 'ab+')

    def _get_file_size(self, file) -> int:
        current_pos = file.tell()
        file.seek(0, 2)
        size = file.tell()
        file.seek(current_pos)
        return size

    def get_index_size(self) -> int:
        return self._get_file_size(self.index_file)

    def get_input_size(self) -> int:
        return self._get_file_size(self.bibel_file)

    def load_kapitel(self, seek: int = None) -> BibelKapitel:
        if seek is not None:
            self.bibel_file.seek(seek)
        line = self.bibel_file.readline().decode('utf-8')
        return BibelKapitel.parse_raw(line)

    def _iterate_specific_kapitel(self, seek_points: Iterable[int]) -> Iterable[BibelKapitel]:
        for seek_point in seek_points:
            yield self.load_kapitel(seek_point)

    def _iterate_kapitel(self) -> Tuple[int, int, BibelKapitel]:
        self.bibel_file.seek(0)
        i = -1
        while True:
            position = self.bibel_file.tell()
            line = self.bibel_file.readline()
            i += 1
            if len(line) < 1:
                break
            kapitel = BibelKapitel.parse_raw(line.decode('utf-8'))
            yield i, position, kapitel

    def _read_int(self, num_bytes: int, seek: int = None) -> int:
        """
        Read bytes from file and return integer.
        :param num_bytes: number of bytes to read
        :param seek: start byte to seek to, if empty, continue where the cursor currently is
        :return: integer converted from byte buffer
        """
        if seek is not None:
            self.index_file.seek(seek)

        buffer = self.index_file.read(num_bytes)
        return int.from_bytes(buffer, byteorder=sys.byteorder)

    def _int2bytes(self, number: int, num_bytes: int) -> bytes:
        """
        Diese Methode bekommt ein int `number` und konvertiert es
        in bytes der Länge `num_bytes`.
        """
        return number.to_bytes(length=num_bytes, byteorder=sys.byteorder, signed=False)

    def _read_token(self, seek: int = None) -> str:
        if seek is not None:
            self.index_file.seek(seek)

        buffer = b''
        while True:
            b = self.index_file.read(1)
            if b == b'':
                raise EOFError('Reached end of index file #EOF')
            if b == self.DELIMITER:
                return buffer.decode('utf-8')
            else:
                buffer += b

    def iterate_postings(self, num_postings, seek: int = None, conflict_safe=False) -> Iterable[Posting]:
        if seek is not None:
            self.index_file.seek(seek)
        position_lock = self.index_file.tell()
        for n in range(num_postings):
            if conflict_safe:
                self.index_file.seek(position_lock)
            doc = self._read_int(4)
            pos = self._read_int(2)
            position_lock = self.index_file.tell()
            yield Posting(document=doc, position=pos)

    def _iterate_index(self, include_offset=False) -> Union[Iterable[Tuple[str, int, Iterable[Posting]]],
                                                            Iterable[Tuple[str, int, int, Iterable[Posting]]]]:
        self.index_file.seek(0)
        try:
            while True:
                token = self._read_token()
                num_postings = self._read_int(3)
                if include_offset:
                    file_offset = self.index_file.tell()
                    yield token, file_offset, num_postings, self.iterate_postings(num_postings)
                else:
                    yield token, num_postings, self.iterate_postings(num_postings)
        except EOFError:
            pass

    def get_index_lookup(self) -> Dict[str, IndexPointer]:
        lookup = dict()
        for token, offset, num_postings, postings in self._iterate_index(include_offset=True):
            lookup[token] = IndexPointer(offset=offset, num_postings=num_postings)
            for _ in postings:  # have to read postings to get to next token
                pass
        return lookup

    def _posting2bytes(self, posting: Posting) -> bytes:
        ret = b''
        ret += self._int2bytes(posting.document, 4)
        ret += self._int2bytes(posting.position, 2)
        return ret

    def _merge_index(self):
        logger.debug('Merging in-memory index to disk.')
        start_time = time.time()

        temp_index_file = open(f'{self.index_filename}.tmp', 'wb+')

        stored_index = self._iterate_index()
        temp_index = self.temp_index.iterate_index()

        stored_token, num_stored_postings, stored_postings = next(stored_index, (None, 0, None))
        temp_token, num_temp_postings, temp_postings = next(temp_index, (None, 0, None))

        def start_token(token, num_postings):
            temp_index_file.write(token.encode('utf-8') + self.DELIMITER)
            temp_index_file.write(self._int2bytes(num_postings, 3))

        def write_posting(posting):
            temp_index_file.write(self._posting2bytes(posting))

        while True:
            if stored_token is None and temp_token is None:
                break

            # both tokens match, merge their postings
            if stored_token == temp_token:
                start_token(stored_token, num_stored_postings + num_temp_postings)
                # print('==', num_stored_postings, num_temp_postings, stored_token)

                stored_posting = next(stored_postings, None)
                temp_posting = next(temp_postings, None)

                while True:
                    if temp_posting is None and stored_posting is None:
                        break

                    if (temp_posting is not None) and (stored_posting is None or
                                                       temp_posting.document < stored_posting.document):
                        write_posting(temp_posting)
                        temp_posting = next(temp_postings, None)
                    elif (stored_posting is not None) and (temp_posting is None or
                                                           temp_posting.document >= stored_posting.document):
                        write_posting(stored_posting)
                        stored_posting = next(stored_postings, None)

                stored_token, num_stored_postings, stored_postings = next(stored_index, (None, 0, None))
                temp_token, num_temp_postings, temp_postings = next(temp_index, (None, 0, None))

            elif (stored_token is not None) and (temp_token is None or stored_token < temp_token):
                start_token(stored_token, num_stored_postings)
                # print('s', num_stored_postings, stored_token)
                for stored_posting in stored_postings:
                    write_posting(stored_posting)
                stored_token, num_stored_postings, stored_postings = next(stored_index, (None, 0, None))

            elif stored_token is None or stored_token >= temp_token:
                start_token(temp_token, num_temp_postings)
                # print('t', num_temp_postings, temp_token)
                for temp_posting in temp_postings:
                    write_posting(temp_posting)
                temp_token, num_temp_postings, temp_postings = next(temp_index, (None, 0, None))

        os.replace(temp_index_file.name, self.index_filename)
        self.index_file = temp_index_file
        used_time = time.time() - start_time
        logger.debug(f'Index merger done in {used_time:.3f}s')

    def read_docs(self):
        # clear (existing?) index file
        self.index_file.seek(0)
        self.index_file.truncate()

        bible_size = self.get_input_size()

        # iterate documents (here: bible chapters)
        for i, file_position, kapitel in self._iterate_kapitel():
            logger.debug(f'Processing "{kapitel.buch}" - {kapitel.kapitel}, '
                         f'file position: {file_position} ({(file_position / bible_size * 100):.2f}%)')
            start_time = time.time()
            # get text and apply pre-processing
            tokens = self.text_processing(kapitel.text)

            num_tokens = 0
            # iterate remaining normalised tokens in document
            for text_position, token in enumerate(tokens):
                num_tokens += 1
                try:
                    # add posting to in-memory index
                    self.temp_index.add(token, Posting(document=file_position, position=text_position))
                except MemoryFullError:
                    # when the index is full, flush-merge it to disk and clear it
                    self._merge_index()
                    self.temp_index.clear()
            used_time = time.time() - start_time
            logger.debug(f'Document had {num_tokens}, took {used_time:.3f}s @ {(num_tokens / used_time):.2f}tps | '
                         f'in-memory index contains {len(self.temp_index)} entries')

        # reading probably doesn't exactly finish with full index, so flush-merge rest to disk
        self._merge_index()

    def text_processing(self, raw_text) -> Iterable[str]:
        tokens = raw_text
        for processor in self.pre_processing_pipeline:
            tokens = processor.process_doc(tokens)
        yield from tokens
