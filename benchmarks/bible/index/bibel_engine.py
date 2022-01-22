from index import TextProcessor, BibelKapitel, BibelReferenz, BibelVers
from pydantic import AnyHttpUrl, BaseModel
from typing import Iterable, List, Optional, Tuple, Union
import re
import logging
from log import except2str
import string


class SimpleTokenizer(TextProcessor):
    def process_doc(self, src: str) -> Iterable[str]:
        """
        Diese Funktion bekommt eine Zeichenkette und teilt diese in einzelne Token auf.
        Jedes erkannte Token wird einzeln via yield zurückgegeben.
        """
        # heavily inspired by
        # https://github.com/RaRe-Technologies/gensim/blob/develop/gensim/parsing/preprocessing.py
        src = src.lower()
        src = src.replace('ä', 'oe')
        src = src.replace('ö', 'oe')
        src = src.replace('ü', 'oe')
        src = src.replace('ß', 'ss')
        src = re.sub(r'([%s])+' % re.escape(string.punctuation), ' ', src)
        src = re.sub(r'\s+', ' ', src)
        src = re.sub(r'[^a-zA-Z\- ]+', '', src)
        for token in src.split():
            yield token


class ShortTokenFilter(TextProcessor):
    def __init__(self, min_len=3):
        self.min_len = min_len

    def process_doc(self, src: Iterable[str]) -> Iterable[str]:
        """
        Diese Funktion erwartet eine Liste an Tokens.
        Es werden nur die Token einzeln via yield zurückgegeben, die eine minimale Länge überschreiten.
        """
        for token in src:
            if len(token) > self.min_len:
                yield token


class StopwordFilter(TextProcessor):
    def __init__(self, stopword_file):
        with open(stopword_file, 'r') as f:
            self.stopwords = set([stopword.strip() for stopword in f])

    def process_doc(self, src: Iterable[str]) -> Iterable[str]:
        """
        Diese Funktion erwartet eine Liste an Tokens.
        Es werden nur die Token einzeln via yield zurückgegeben, die nicht in einer
        Liste an Stopwörtern vorkommen.
        """
        for token in src:
            if token not in self.stopwords:
                yield token


class CustomStemmer(TextProcessor):

    def process_doc(self, src: Iterable[str]) -> Iterable[str]:
        """
        Hier können Sie einen beliebigen eigenen Stemmer oder Lemmatiser bauen.
        """
        for token in src:
            yield token


class CISTEMStemmer(TextProcessor):
    # heavily inspired by https://github.com/LeonieWeissweiler/CISTEM/blob/master/Cistem.py
    strip_ge = re.compile(r"^ge(.{4,})")
    repl_xx = re.compile(r"(.)\1")
    repl_xx_back = re.compile(r"(.)\*")
    strip_emr = re.compile(r"e[mr]$")
    strip_nd = re.compile(r"nd$")
    strip_t = re.compile(r"t$")
    strip_esn = re.compile(r"[esn]$")

    def __init__(self, case_insensitive=False):
        self.case_insensitive = case_insensitive

    def process_doc(self, src: Iterable[str]) -> Iterable[str]:
        for token in src:
            yield self.process_word(token)

    def process_word(self, wort: str) -> str:
        """
        Diese Funktion erwartet ein einzelnes Token und gibt dieses nach Anwendung des CISTEM Algorithmus zurück.
        Der Algorithmus wird in Abbildung 5 in der Veröffentlichung
            Developing a Stemmer for German Based on a Comparative Analysis of Publicly Available Stemmers
            Leonie Weißweiler, Alexander Fraser, 2017
        beschrieben.
        Link zum PDF: https://www.cis.uni-muenchen.de/~weissweiler/cistem/
        """
        if len(wort) == 0:
            return wort

        upper = wort[0].isupper()
        wort = wort.lower()

        wort = wort.replace("ü", "u")
        wort = wort.replace("ö", "o")
        wort = wort.replace("ä", "a")
        wort = wort.replace("ß", "ss")

        wort = self.strip_ge.sub(r"\1", wort)
        wort = wort.replace("sch", "$")
        wort = wort.replace("ei", "%")
        wort = wort.replace("ie", "&")
        wort = self.repl_xx.sub(r"\1*", wort)

        while len(wort) > 3:
            if len(wort) > 5:
                (wort, success) = self.strip_emr.subn("", wort)
                if success != 0:
                    continue

                (wort, success) = self.strip_nd.subn("", wort)
                if success != 0:
                    continue

            if not upper or self.case_insensitive:
                (wort, success) = self.strip_t.subn("", wort)
                if success != 0:
                    continue

            (wort, success) = self.strip_esn.subn("", wort)
            if success != 0:
                continue
            else:
                break

        wort = self.repl_xx_back.sub(r"\1\1", wort)
        wort = wort.replace("%", "ei")
        wort = wort.replace("&", "ie")
        wort = wort.replace("$", "sch")

        return wort


class PorterStemmer(TextProcessor):
    vokale = set('aeiouyäüö')
    konsonanten = set('bcdfghjklmnpqrstvwxzßUY')
    s_endung = set('bdfghklmnrt')
    st_endung = set('bdfghklmnt')
    stopliste = {'aber', 'alle', 'allem', 'allen', 'aller', 'alles', 'als', 'also', 'am', 'an', 'ander', 'andere',
                 'anderem', 'anderen', 'anderer', 'anderes', 'anderm', 'andern', 'anders', 'auch', 'auf', 'aus', 'bei',
                 'bin', 'bis', 'bist', 'da', 'damit', 'dann', 'der', 'den', 'des', 'dem', 'die', 'das', 'dass', 'daß',
                 'derselbe', 'derselben', 'denselben', 'desselben', 'demselben', 'dieselbe', 'dieselben', 'dasselbe',
                 'dazu', 'dein', 'deine', 'deinem', 'deinen', 'deiner', 'deines', 'denn', 'derer', 'dessen', 'dich',
                 'dir', 'du', 'dies', 'diese', 'diesem', 'diesen', 'dieser', 'dieses', 'doch', 'dort', 'durch', 'ein',
                 'eine', 'einem', 'einen', 'einer', 'eines', 'einig', 'einige', 'einigem', 'einigen', 'einiger',
                 'einiges', 'einmal', 'er', 'ihn', 'ihm', 'es', 'etwas', 'euer', 'eure', 'eurem', 'euren', 'eurer',
                 'eures', 'für', 'gegen', 'gewesen', 'hab', 'habe', 'haben', 'hat', 'hatte', 'hatten', 'hier', 'hin',
                 'hinter', 'ich', 'mich', 'mir', 'ihr', 'ihre', 'ihrem', 'ihren', 'ihrer', 'ihres', 'euch', 'im', 'in',
                 'indem', 'ins', 'ist', 'jede', 'jedem', 'jeden', 'jeder', 'jedes', 'jene', 'jenem', 'jenen', 'jener',
                 'jenes', 'jetzt', 'kann', 'kein', 'keine', 'keinem', 'keinen', 'keiner', 'keines', 'können', 'könnte',
                 'machen', 'man', 'manche', 'manchem', 'manchen', 'mancher', 'manches', 'mein', 'meine', 'meinem',
                 'meinen', 'meiner', 'meines', 'mit', 'muss', 'musste', 'muß', 'mußte', 'nach', 'nicht', 'nichts',
                 'noch', 'nun', 'nur', 'ob', 'oder', 'ohne', 'sehr', 'sein', 'seine', 'seinem', 'seinen', 'seiner',
                 'seines', 'selbst', 'sich', 'sie', 'ihnen', 'sind', 'so', 'solche', 'solchem', 'solchen', 'solcher',
                 'solches', 'soll', 'sollte', 'sondern', 'sonst', 'über', 'um', 'und', 'uns', 'unse', 'unsem', 'unsen',
                 'unser', 'unses', 'unter', 'viel', 'vom', 'von', 'vor', 'während', 'war', 'waren', 'warst', 'was',
                 'weg', 'weil', 'weiter', 'welche', 'welchem', 'welchen', 'welcher', 'welches', 'wenn', 'werde',
                 'werden', 'wie', 'wieder', 'will', 'wir', 'wird', 'wirst', 'wo', 'wollem', 'wollte', 'würde', 'würden',
                 'zu', 'zum', 'zur', 'zwar', 'zwischen'}

    def __init__(self, use_stopwords=False):
        self.use_stopwords = use_stopwords

    def process_doc(self, src: Iterable[str]) -> Iterable[str]:
        for token in src:
            yield self.process_word(token)

    def process_word(self, wort: str) -> str:
        """
        Diese Funktion erwartet ein einzelnes Token und gibt dieses nach Anwendung des Porter Algorithmus zurück.
        Originale Veröffentlichung: https://www.cs.odu.edu/~jbollen/IR04/readings/readings5.pdf
        Adaption der Regeln für Deutsch: http://snowball.tartarus.org/algorithms/german/stemmer.html

        Keine Garantie, dass diese Implementierung perfekt korrekt ist...
        Dieser Code ist eine Übersetzung/Vereinfachung der Referenzimplementierung:
           http://snowball.tartarus.org/otherlangs/german_py.txt
        """
        if self.use_stopwords and (wort in self.stopliste):
            return wort

        wort = wort.replace('ß', 'ss')

        # Schützenswerte 'u' bzw. 'y' werden durch 'U' bzw. 'Y' ersetzt
        if 'u' in wort or 'y' in wort:
            for i, char in enumerate(wort):
                if i == 0 or i + 1 == len(wort):
                    continue
                if char == 'u' and wort[i - 1] in self.vokale and wort[i + 1] in self.vokale:
                    wort = wort[:i] + 'U' + wort[i + 1:]
                if char == 'y' and wort[i - 1] in self.vokale and wort[i + 1] in self.vokale:
                    wort = wort[:i] + 'Y' + wort[i + 1:]

        # r1, r2, p1 & p2 werden mit Werten belegt
        p1 = 0
        r1 = ''
        hat_vokal = False
        for i, char in enumerate(wort):
            if char in self.vokale:
                hat_vokal = True
            if char in self.konsonanten and hat_vokal:
                p1 = i + 1
                r1 = wort[p1:]
                break
        p2 = 0
        r2 = ''
        hat_vokal = False
        for i, char in enumerate(r1):
            if char in self.vokale:
                hat_vokal = True
            if char in self.konsonanten and hat_vokal:
                p2 = i + 1
                r2 = r1[p2:]
                break

        if 0 < p1 < 3:
            p1 = 3
            r1 = wort[p1:]
        if p1 == 0:
            return self.end_stemming(wort)

        # Schritt 1
        for suffix in ['e', 'em', 'en', 'ern', 'er', 'es']:
            suffix_len = len(suffix)
            if suffix == r1[-suffix_len:]:
                wort = wort[:-suffix_len]
                r1 = r1[:-suffix_len]
                r2 = r2[:-suffix_len]
                break
        else:  # only if loop didn't break
            if len(wort) >= 2 and len(r1) > 0 and \
                    r1[-1] == 's' and wort[-2] in self.s_endung:
                wort = wort[:-1]
                r1 = r1[:-1]
                r2 = r2[:-1]

        # Schritt 2
        for suffix in ['est', 'er', 'en']:
            suffix_len = len(suffix)
            if suffix == r1[-suffix_len:]:
                wort = wort[:-suffix_len]
                r1 = r1[:-suffix_len]
                r2 = r2[:-suffix_len]
                break
        else:  # only if loop didn't break
            if len(wort) > 5 and r1[-2:] == 'st' and wort[-3] in self.st_endung:
                wort = wort[:-2]
                r1 = r1[:-2]
                r2 = r2[:-2]

        # Schritt 3a)
        for suffix in ['end', 'ung']:
            suffix_len = len(suffix)
            if suffix == r2[-suffix_len:]:
                if 'ig' == r2[-suffix_len + 2:-suffix_len]:
                    if 'e' == wort[-suffix_len + 3]:
                        wort = wort[:-suffix_len]
                        r1 = r1[:-suffix_len]
                        r2 = r2[:-suffix_len]
                        break
                    else:
                        wort = wort[:-suffix_len + 2]
                        r1 = r1[:-suffix_len + 2]
                        r2 = r2[:-suffix_len + 2]
                        break
                else:
                    wort = wort[:-suffix_len]
                    r1 = r1[:-suffix_len]
                    r2 = r2[:-suffix_len]
                return self.end_stemming(wort)

        # Schritt 3b)
        for suffix in ['ig', 'ik', 'isch']:
            suffix_len = len(suffix)
            if suffix == r2[-suffix_len:]:
                if 'e' != wort[-suffix_len + 1]:
                    wort = wort[:-suffix_len]
                    r1 = r1[:-suffix_len]
                    r2 = r2[:-suffix_len]
                    break

        # Schritt 3c)
        for suffix in ['lich', 'keit']:
            suffix_len = len(suffix)
            if suffix == r2[-suffix_len:]:
                for suffix2 in ['er', 'en']:
                    suffix2_len = len(suffix2)
                    if suffix2 == r1[-(suffix_len + suffix2_len):-suffix_len]:
                        wort = wort[:-(suffix_len + suffix2_len)]
                        r1 = r1[:-(suffix_len + suffix2_len)]
                        r2 = r2[:-(suffix_len + suffix2_len)]
                        break
                else:  # only run if loop didn't break
                    wort = wort[:-suffix_len]
                    r1 = r1[:-suffix_len]
                    r2 = r2[:-suffix_len]
                    break

        # Schritt 3d)
        for suffix in ['keit']:
            suffix_len = len(suffix)
            if suffix == r2[-suffix_len:]:
                for suffix2 in ['lich', 'ig']:
                    suffix2_len = len(suffix2)
                    if suffix2 == r2[-(suffix_len + suffix2_len):-suffix_len]:
                        wort = wort[:-(suffix2_len + suffix_len)]
                        break
                else:  # only run if loop didn't break
                    wort = wort[:-suffix_len]
                    break
        return self.end_stemming(wort)

    def end_stemming(self, wort):
        wort = wort.replace('ä', 'a')
        wort = wort.replace('ö', 'o')
        wort = wort.replace('ü', 'u')
        wort = wort.replace('U', 'u')
        wort = wort.replace('Y', 'y')
        return wort
