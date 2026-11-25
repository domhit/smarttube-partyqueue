# Migration auf V4/V4.5

1. `data/partyqueue.db` sichern.
2. Den aktuellen PartyQueue-SmartTube-Fork auf den Zielgeräten installieren.
3. In SmartTube die REST API aktivieren und Port, Benutzer und Passwort festlegen.
4. In PartyQueue unter **Host → TVs** dieselben REST-Zugangsdaten hinterlegen.
5. Für jedes Gerät **REST testen** ausführen.
6. `./adb:/root/.android` weiterhin persistent einbinden. ADB wird in V4.5 nur noch für SmartTube-Bootstrap/Recovery verwendet.
7. Optional SmartTube Events konfigurieren: PartyQueue-URL, Device-ID und gemeinsamer Event-Token.
8. Erst danach eine Testparty starten und im Debug-Tab Queue und Playback prüfen.

Die REST API ist der primäre Transport. `/api/playback/progress` aus älteren Home-Assistant-Ständen ist in V4 nicht mehr aktiv.
