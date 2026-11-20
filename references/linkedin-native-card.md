# Die native LinkedIn Business Card – Faktenstand

**Stand: 20.11.2026.** Die Funktion wird schrittweise ausgerollt. Vor jeder Aussage gegenüber Nutzern prüfen, ob die Hilfeseite neuer ist (Datum „Last updated“), und diese Datei dann mit Datum aktualisieren.

## Quellen

| Quelle | Art | Stand |
| --- | --- | --- |
| [LinkedIn-Hilfe a16648713 „LinkedIn Business Card“](https://www.linkedin.com/help/linkedin/answer/a16648713) | offiziell | gelesen 20.11.2026 („Last updated: 1 week ago“) |
| [LinkedIn Newsroom, 15.10.2026: „New Ways to Build Meaningful Connections …“](https://news.linkedin.com/2026/new-ways-to-build-meaningful-connections) | offiziell | veröffentlicht 15.10.2026 |
| Forbes (W. Arruda, 20.10.2026), ConnectMachine-Vergleich (19.11.2026), Beiträge von Nutzern | Dritte | nur ergänzend |

Hinweis für Agenten: `news.linkedin.com` und `linkedin.com/help` lassen sich mit Firecrawl nicht abrufen, mit einem einfachen WebFetch dagegen schon.

## Offiziell belegt

**Was die Karte ist.** Eine digitale Visitenkarte aus dem eigenen Profil. Sie hat eine Vorder- und eine Rückseite, die getrennt gestaltet werden (*„LinkedIn Business Card has a front and a back, which you can customize separately.“*).

**Plattform und Sprache.** *„This feature is available only on the LinkedIn mobile app in English.“* Laut LinkedIn sollen weitere Geräte und Sprachen folgen. Die weltweite Einführung läuft *„over the coming months“* (Newsroom).

**Öffnen.** Oben links auf das Profilfoto tippen, dann oben im Profil auf den QR-Code tippen. Durch Wischen wechselt man zwischen Vorder- und Rückseite.

**Bearbeiten.** Auf *Edit* tippen. Die Optionen liegen unten am Bildschirm. Zum Schluss *Save* tippen.

| Option | Was sie steuert (Hilfetext) |
| --- | --- |
| **Info** | Headline hinzufügen oder ändern. Häkchen bei *Company or school* und *Location* (beides optional) |
| **Layout** | Kartenlayout und Stil des Profilfotos |
| **Font** | Schriftstil der Karte |
| **Colors** | Farben der Karte. Doppeltippen auf die Farbauswahl wechselt zwischen Vorder- und Rückseite |
| **Pattern** | Muster der Karte |
| **Stickers and Doodle** | Sticker, Fotos als Ausschnitt (*cutouts*), Zeichnungen wie eine Unterschrift. **Nur auf der Rückseite.** Verschieben per Ziehen, Größe und Drehung mit zwei Fingern, Löschen über *Tap and hold* → *Delete* |

**Inhalte der Karte.** Profilfoto (mit Fotostil), Name, Headline, optional Firma oder Schule und Ort. Telefon und E-Mail erwähnt die Hilfe **nicht**.

**Austausch.** Zwei Wege:

1. Gegenseitig die Karten scannen.
2. *Auto-swap when you scan*. Einstellung: *More* → *Share settings*. Dort lässt sich die eigene Karte auch aus allen Sammlungen entfernen (*Remove your card from everyone's collections*).

**Kein automatisches Vernetzen.** *„Exchanging cards doesn't automatically send a connection request or follow the member.“*

**Sammlung.** Erhaltene Karten liegen unter *My Network* → *Manage My Network* → *Business Cards*. Ändert jemand seine Karte, aktualisiert sie sich auch in den Sammlungen anderer.

**Wallet.** *„You can add your LinkedIn Business Card to your phone's Apple or Google wallet“*. Dafür auf *Add to Wallet* tippen.

## Nicht belegt bzw. nicht vorhanden (Stand 20.11.2026)

- **Keine API und keine Web-Version.** Die Karte lässt sich nicht automatisch erstellen oder befüllen.
- **Keine eigenen Hex-Farben, kein eigenes Logo-Feld, kein Datei-Export** werden erwähnt. Für ein Logo bleibt nur ein Foto-Ausschnitt auf der Rückseite.
- **Anzahl und Namen** der Layouts, Schriften, Farben und Muster sind nicht dokumentiert. Darum nennen Anleitungen die Farbfamilie und den nächstliegenden Hex-Wert, keine erfundenen Optionsnamen.
- **Kosten:** Die Hilfe nennt keine. Ein Premium-Bezug ist nicht belegt; die private „Profil-Notiz“-Funktion aus derselben Ankündigung ist Premium und eine andere Funktion.

## Folgen für diesen Skill

1. **Native Karte:** Der Skill erzeugt eine Klick-Anleitung (`linkedin-native-card.md`), die das CI in die verfügbaren Optionen übersetzt.
2. **Eigene Karte:** Für alles, was LinkedIn nicht kann (exakte CI-Farben, Logo, Kontaktfelder, Druck, Teilen-Bild), rendert der Skill eine eigene Karte. Deren QR-Code führt zum selben Profil.
3. **Wallet-Pässe** baut der Skill nicht. Apple verlangt ein Pass-Type-Zertifikat, Google ein Issuer-Konto. Den Wallet-Weg deckt die native Karte ab.
