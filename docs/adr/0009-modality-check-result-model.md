# ADR 0009: Ein Testlauf mit eingebetteten Modality-Subresultaten

## Status

Akzeptiert

## Kontext

Eine Modalitätsprüfung besteht aus MWL und Store, soll aber in der Historie als ein manueller Vorgang erscheinen. Eine normalisierte Parent-/Child-Struktur wäre für den kleinen lokalen Anwendungsfall unnötig komplex.

## Entscheidung

Der Check speichert einen `test_runs`-Eintrag vom Typ `modality_check`. `result_json` enthält Profilbezug, Gesamtergebnis und getrennte Worklist-/Store-Subresultate. Das Gesamtergebnis ist nur erfolgreich, wenn alle aktivierten Subchecks erfolgreich sind. Worklist-Trefferlisten werden nicht in diesem kombinierten Lauf persistiert.

## Konsequenzen

Partielle Fehler bleiben klar sichtbar, während Filterung und Historie einfach bleiben. Strukturänderungen an Subresultaten müssen abwärtskompatibel gelesen werden.
