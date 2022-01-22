# Übungsblatt 3

Abgabe von 796854  
weiteres Gruppenmitglied: 796395

## 1

### a

Wenn man Anfrageteile mit "oder" verbindet, kann es sehr schnell zu sehr vielen Ergebnissen kommen. Vor allem weil die Ergebnisse auch nicht gerankt werden, ist das nachteilig.

### b

Zum einen werden Suchoperatoren oft implizit verwendet. Wenn man z. B. nach "Jaguar" sucht, Ergebnisse zum Auto findet, und danach seine Suchanfrage zu "Jaugar Tier" spezifiziert, erwartet man, dass nur Dokumente angezeigt werden, die sowohl Jaguars als auch Tiere behandeln. Das Genauer-Spezifizieren, das viele Menschen beim Suchen mit mehreren Begriffen machen, ist basically ein implizites Verwenden von Suchoperatoren.

Wenn jemand professionell eine Suchmaschine nutzt, aber sich nicht in der Lage findet, bestimmte Suchergebnislisten zu kombinieren, kann das sehr frustrierend sein. (Wenn man z. B. zwei Suchergebnislisten kombinieren oder filtern will.)
Die Unterstützung von Booleschen Operatoren ermöglicht es einem professionellen Sucher, Ergebnislisten auf *jede erdenkliche Art* zu kombinieren. Das machen nicht viele Menschen, aber denjenigen, die das machen und brauchen, erspart es eine Menge Frustration.

### c

Bei Kontexten wo man eine bestimmte Entität sucht, ist eine Precision-Orientierte Suchmaschine meist besser. Das trifft z.B. bei Produktsuchmaschinen zu, bei der man meist bereits weiß, was man kaufen will, und ein ganz bestimmtes Produkt sucht.  
Bei einer Explore-Suche in einer Musikapp möchte man vielleicht eher von einem breiteren Angebot zum gesuchtem Genre inspiriert werden. Dabei ist dann eine Recall-Orientierte Suche besser. (Will man ein ganz bestimmtes Stück suchen, aber wieder eher eine Precision-Orientierte).

## 2

$1$ steht für $\text{true}$, $0$ für $\text{false}$.

### a

$D_1: (t_1 \lor t_5) \land \neg t_2 \equiv
(1 \lor 1) \land \neg 0 \equiv
1 \land 1 \equiv
1$  
$D_2: (t_1 \lor t_5) \land \neg t_2 \equiv
(1 \lor 1) \land \neg 1 \equiv
1 \land 0 \equiv
0$  
$D_3: (t_1 \lor t_5) \land \neg t_2 \equiv
(0 \lor 0) \land \neg 0 \equiv
0 \land 1 \equiv
0$  
$D_4: (t_1 \lor t_5) \land \neg t_2 \equiv
(0 \lor 1) \land \neg 0 \equiv
1 \land 1 \equiv
1$  
$D_5: (t_1 \lor t_5) \land \neg t_2 \equiv
(0 \lor 1) \land \neg 0 \equiv
1 \land 1 \equiv
1$  
$D_6: (t_1 \lor t_5) \land \neg t_2 \equiv
(1 \lor 0) \land \neg 1 \equiv
1 \land 0 \equiv
0$

### b

$D_1: (t_1 \land t_5) \lor (t_3 \land t_2) \equiv
(1 \land 1) \lor (0 \land 0) \equiv
1 \lor 0 \equiv
1$  
$D_2: (t_1 \land t_5) \lor (t_3 \land t_2) \equiv
(1 \land 1) \lor (0 \land 1) \equiv
1 \lor 0 \equiv
1$  
$D_3: (t_1 \land t_5) \lor (t_3 \land t_2) \equiv
(0 \land 0) \lor (1 \land 0) \equiv
0 \lor 0 \equiv
0$  
$D_4: (t_1 \land t_5) \lor (t_3 \land t_2) \equiv
(0 \land 1) \lor (0 \land 0) \equiv
0 \lor 0 \equiv
0$  
$D_5: (t_1 \land t_5) \lor (t_3 \land t_2) \equiv
(0 \land 1) \lor (1 \land 0) \equiv
0 \lor 0 \equiv
0$  
$D_6: (t_1 \land t_5) \lor (t_3 \land t_2) \equiv
(1 \land 0) \lor (0 \land 1) \equiv
0 \lor 0 \equiv
0$  

## 3

### a

| x   |     | J   | E   | S   | U   | S   |
| --- | --- | --- | --- | --- | --- | --- |
|     | `0` | 1   | 2   | 3   | 4   | 5   |
| J   | 1   | `0` | 1   | 2   | 3   | 4   |
| O   | 2   | `1` | 2   | 3   | 4   | 5   |
| H   | 3   | `2` | 3   | 4   | 5   | 6   |
| A   | 4   | `3` | 4   | 5   | 6   | 7   |
| N   | 5   | `4` | 5   | 6   | 7   | 8   |
| N   | 6   | `5` | 6   | 7   | 8   | 9   |
| E   | 7   | 6   | `5` | 6   | 7   | 8   |
| S   | 8   | 7   | 6   | `5` | `6` | `7` |

Die andere, grau hinterlegte Schrift markiert den gewählten Weg.

### b

Bei Google und Bing muss man "University of P" eingeben, um "University of Potsdam" als Vorschlag zu bekommen.
Bei DuckDuckGo muss man etwas mehr tippen – "University of Pot".
Bei Yandex werden ab "University of Pot" gar keine Vorschläge mehr angezeigt, also muss man die Suchanfrage vollständig eintippen.

| Google                | DuckDuckGo                    |
| --------------------- | ----------------------------- |
| ![google](google.jpg) | ![duckduckgo](duckduckgo.jpg) |

| Bing              | Yandex                |
| ----------------- | --------------------- |
| ![bing](bing.jpg) | ![yandex](yandex.jpg) |

### c

Dem Element Baryllium können zwar keine gelben Haare wachsen, googelt man aber nach gelbhaarigem Beryllium – in englischer Fachsprache "xanthocomic Beryllium" – gibt es aber doch einen Treffer:

![xanthocomic beryllium](xanthocomic_beryllium.png)
<small>Suche im Inkognito-Modus. Keiner der Suchbegriffe fängt mit Q an.</small>

## 4

### e

> Um die konjunktive Suche in `grep` zu ermöglichen, wurden die Befehle gepiped (z. B. für "der Himmel" `grep der results.json | grep -c himmel`). Die `-c`-Option sorgt dafür, dass nur der Count ausgegeben wird, die Laufzeit also nicht überwiegend von der Ausgabe bestimmt wird.

| Suchanfrage          | Ungerankte Non-Positional Queries | Naive Queries | `grep` |
| -------------------- | --------------------------------- | ------------- | ------ |
| Jesus                | 177 ms                            | 6456 ms       | 70 ms  |
| der Himmel           | 324 ms                            | 6437 ms       | 80 ms  |
| es stand geschrieben | 138 ms                            | 6928 ms       | 60 ms  |
| Maria                | 22 ms                             | 7748 ms       | 60 ms  |
| herr                 | 745 ms                            | 8935 ms       | 80 ms  |
| gott                 | 949 ms                            | 8920 ms       | 90 ms  |
| herr gott            | 780 ms                            | 7523 ms       | 80 ms  |
| moses                | 201 ms                            | 7508 ms       | 60 ms  |

Man sieht, dass der naive Ansatz eindeutig der langsamste ist.
Ungerankte non-positional Queries sind schon deutlich schneller – den Index zu erstellen hat sich also gelohnt.
`grep` ist nochmal um einiges schneller – wahrscheinlich, weil es optimierter ist, in C geschrieben ist und durch die Pipes sogar auf mehrere Threads läuft.  
Im Gegensatz dazu ist unsere Python-Suchmaschine aus akademischem Rahmen in Python geschrieben und nicht optimiert springt z. B. in der Datei ständig hin und her.
Eine optimierte Indexsuche ist wahrscheinlich nochmal um einiges schneller als `grep`.

### f

So sieht die Laufzeit (in ms) abhängig von der Query-Länge (in Wörtern) aus:

![benchmark](benchmark.png)
<small>Der Benchmark bei den Standard Non-Positional-Queries. Bei anderen Query-Arten (mit Rankings) sehen die Ergebnisse nicht viel anders aus, deshalb hab ich sie hier mal weggelassen.</small>

Am Anfang ist der Benchmark wohl sehr stark von der Ergebnisgröße abhängig. Wahrscheinlich nimmt das Allozieren der Result-Ergebnisse die meiste Zeit in Anspruch.  
Nach hinten jedoch sieht man, dass es immer weniger Unterschiede zwischen den Queries gibt. Das ist auch verständlich – es muss ja nur einer der Iteratoren wenige Postings haben (aka ein seltenes Wort repräsentieren) und schon ist das Ergebnis superschnell da, weil früh abgebrochen wird.  
Erst bei sehr vielen Iteratoren wird der Graph wieder steigen, weil dann das Ablaufen aller Iteratoren etwas Zeit in Anspruch nimmt. So große Queries begegnen einem im Alltag selten. Eine weitere Situation, bei der die Laufzeit steigen könnte, ist, wenn wir auch nicht-konjunktive Queries erlauben würden. Dann müssten wir nämlich möglicherweise jeden der Iteratoren bis zum Ende durchgehen. 
