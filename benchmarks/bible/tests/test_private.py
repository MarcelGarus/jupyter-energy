import sys
import os

# Wenn man nur diese Datei beim Testen ausführt, sollte man den Ordner wechseln.
# Dazu die folgenden zwei Zeilen auskommentieren.
# myPath = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(1, myPath + '/../')

import logging
from log import init_logging
from tests.data import get_sample, STOPWORD_LIST, DOCUMENTS, INDEX, bibel_index, PRE_PROCESSING, prep_query_results

init_logging('DEBUG')
# logging.disable(logging.DEBUG)

logger = logging.getLogger('test.private')


# Alle Methoden, die mit test_ beginnen werden von pytest ausgeführt.

def test_opus():
    life = 'na na na na na'
    assert life is life

    mystery = ''
    assert mystery is not 'a bird' and mystery is not 'a plane'
    # it must be dave, who's on the train

    # Your coding playlist
    # https://www.youtube.com/watch?v=u9odvl3tfEU
    # https://www.youtube.com/watch?v=eGUsqIPurNQ
    # https://www.youtube.com/watch?v=R5QJVUMARLc
    # https://www.youtube.com/watch?v=tbdRIv3uYrg
    # https://www.youtube.com/watch?v=O64vSP-Zj6U
    # https://www.youtube.com/watch?v=X2WH8mHJnhM
    # https://www.youtube.com/watch?v=8xvkYaldSd0
    # https://www.youtube.com/watch?v=7MniRndBkCU
    # https://www.youtube.com/watch?v=u5NuRpXqhGQ
