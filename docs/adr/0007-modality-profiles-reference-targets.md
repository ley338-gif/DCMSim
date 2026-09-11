# ADR 0007: Modalitätsprofile referenzieren Ziele

## Status

Akzeptiert

## Kontext

Ein Gerät benötigt eine eigene Modalität und Calling AE, verwendet für MWL und Storage aber bereits zentral gepflegte Gegenstellen. Eine Duplizierung von Host, Port und Called AE würde Konfigurationen auseinanderlaufen lassen.

## Entscheidung

`modality_profiles` referenziert optionale MWL- und Store-Targets per Fremdschlüssel. Aktive Dienste verlangen beim Schreiben ein passendes Ziel. Beim Löschen eines Targets werden Referenzen auf `NULL` gesetzt; das Profil bleibt für Diagnose und Reparatur sichtbar, kann aber bis zur Neuzuordnung nicht geprüft werden.

## Konsequenzen

Zieländerungen gelten sofort für alle Profile. Die API muss fehlende oder für den Dienst ungeeignete Ziele validieren. SQLite-Fremdschlüssel werden pro Verbindung aktiviert; die Löschroute nullt Referenzen zusätzlich explizit.
