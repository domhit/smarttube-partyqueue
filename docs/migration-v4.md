# Migration von V3.1 auf V4

1. Vorher `data/partyqueue.db` sichern.
2. SmartTube-REST-Fork auf jedem Zielgerät installieren und die REST API aktivieren.
3. V4 zunächst mit einer Kopie des Datenverzeichnisses starten.
4. Unter **Host > TVs** jedes Gerät bearbeiten und API-Port, Benutzer sowie Passwort ergänzen.
5. Für jedes Gerät **API testen** ausführen.
6. Erst danach eine Testparty starten.

Die Datenbankmigration ergänzt `api_port`, `api_username` und `api_password`. Alte ADB- und Home-Assistant-Spalten bleiben in bestehenden Datenbanken ungenutzt erhalten. Das ADB-Volume wird von V4 nicht mehr benötigt.
