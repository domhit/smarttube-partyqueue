# GitHub Container Registry

Der Workflow `.github/workflows/ghcr.yml` testet und baut Images für `linux/amd64` und `linux/arm64` und veröffentlicht sie unter `ghcr.io/domhit/smarttube-partyqueue`.

## Entwicklungsimages

Pushes auf `develop` oder `develop-v*` erzeugen den jeweiligen Branch-Tag sowie einen `sha-*`-Tag. Der aktuell verwendete Entwicklungsbranch ist `develop`.

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:develop
```

## Release Candidate

Der V4.5 Stable Release wird mit folgendem Git-Tag veröffentlicht:

```bash
git tag -a v4.5.1 -m "SmartTube PartyQueue v4.5.1"
git push origin v4.5.1
```

Danach ist das versionierte Image verfügbar als:

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:4.5.1
```

`docker-compose.ghcr.yml` ist für den RC bewusst auf `4.5.1` festgesetzt. Erst der finale, nach `main` gemergte `v4.5.1`-Release soll als stabiler Produktionsstand dokumentiert werden.

## CI-Prüfungen vor Veröffentlichung

Der GHCR-Workflow hängt vom wiederverwendbaren Testworkflow ab. Vor dem Image-Build laufen Python-Syntax, JavaScript-Syntax, `pytest` und ein Docker-Smoke-Build. Das veröffentlichte Image erhält außerdem Provenance-/SBOM-Metadaten.
