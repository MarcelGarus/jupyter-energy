# Bible benchmark

This program is from the Information Retrieval course and can perform two interesting tasks:

- building a search index for the whole bible
- looking up exact search terms in the bible

The first task can be performed by running `python3 main.py --build-index`. This will take some time and build a `inverted_index.bin` file, which takes up about 2.2 MB.

The second task can be executed using `python3 main.py --speed-comparison`. This will search for some example queries in different ways, using either non-positional index queries, term-frequency-inverse-document-frequency index queries, or a naive approach.

## Original docs from the Information Retrieval course

### Python Umgebung einrichten
Voraussetzung ist, dass Python 3 und pip installiert sind.
Bitte folgen Sie der Anleitung für Ihr jeweiliges Betriebssystem und 
https://virtualenv.pypa.io/en/latest/installation.html

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Auf unserem Testsystem läuft ein auf Arch-Linux basiertes und aktuelles
 Manjaro, dementsprechend Python 3.8.
  
### Testen
Schauen Sie sich die Datei `tests/test_public.py` genau an.
Sie können weitere Funktionen ergänzen. Solche, die mit `test_` beginnen, 
werden als Test ausgeführt.
Für weitere Informationen konsultieren Sie bitte die Dokumentation: 
https://docs.pytest.org/en/latest/

Zum Ausführen der Tests öffnen Sie eine shell in diesem Ordner und 
führen `pytest` aus.

### Ausführen
Öffnen Sie eine shell in diesem ordner und führen Sie `python main.py` aus.
Ihnen wird dann eine Hilfestellung zur korrekten Ausführung angezeigt.

Wenn Sie mit auf einem UNIX System Arbeiten und die Ausführung im Terminal 
starten, können Sie die Ausgabe direkt in eine Datei umleiten. Dabei wird 
das Ergebnis aber erst nach Ende der Ausführung geschrieben.

Mit `python -b main.py > log.txt` können Sie ungepuffert loggen und 
gleichzeitig in einem anderen Terminal mit `tail -f log.txt` die Ausgabe 
verfolgen. Oder Sie nutzen `python -b main.py | tee log.txt`. In PyCharm können
Sie den log auch speichern. Öffnen Sie hierzu 

### Abgeben

Verpacken des Ordners, der alle Daten aus der Vorlage enthält, die
bearbeiteten Dateien in-place lassen. Gegebenenfalls zusätzliche Skripte 
müssen dokumentiert und in der Abgabe-PDF vermerkt sein, wenn sie relevant sind.

```shell script
cp /path/to/Uebung_03/Praktikum_Template /path/to/Uebung_03/Praktikum
# Aufgaben implementieren
cd /path/to/Uebung_03/Praktikum/
zip uebung03.zip -r . -x 'run.log' -x '*__pycache__/*' -x '*.pytest_cache/*' -x 'inverted_index.bin.bak'
```

Die exclude Liste sollten Sie entsprechend erweitern.

Um zu schauen, ob man unnötige Dateien und Ordner abgibt, 
kann man den Inhalt des zip Archivs anschauen: `unzip -l uebung03.zip`.

### German Stopword List
Für die Wörter in stopwords.txt gibt es folgende Lizenzinformation:
```
; GERMAN STOPWORDS  
; Zusammmengetragen von Marco Götze, Steffen Geyer  
; LAST UPDATE 12/2016  
; Web Stopwords, more information at Source Link below!  
; www.solariz.de  
; Source and more Information: https://solariz.de/de/downloads/6/german-enhanced-stopwords.htm  
; Taken from https://github.com/solariz/german_stopwords/blob/master/german_stopwords_plain.txt  
; ####  
; Link-Ware; If you use this List somehow please give me a Link to URL mentioned above! Thanks  
; ####  
```