# GitHub Container Registry

Der Workflow `.github/workflows/ghcr.yml` testet und baut Images für `linux/amd64` und `linux/arm64` und veröffentlicht sie unter `ghcr.io/domhit/smarttube-partyqueue`.

## Entwicklungsimages

Pushes auf `develop` oder `develop-v*` erzeugen den jeweiligen Branch-Tag sowie einen `sha-*`-Tag. Der aktuell verwendete Entwicklungsbranch ist `develop-v4`.

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:develop-v4
```

## Release Candidate

Der V4.5 Release Candidate wird mit folgendem Git-Tag veröffentlicht:

```bash
git tag -a v4.5.0-rc1 -m "SmartTube PartyQueue v4.5.0-rc1"
git push origin v4.5.0-rc1
```

Danach ist das versionierte Image verfügbar als:

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:4.5.0-rc1
```

`docker-compose.ghcr.yml` ist für den RC bewusst auf `4.5.0-rc1` festgesetzt. Erst der finale, nach `main` gemergte `v4.5.0`-Release soll als stabiler Produktionsstand dokumentiert werden.

## CI-Prüfungen vor Veröffentlichung

Der GHCR-Workflow hängt vom wiederverwendbaren Testworkflow ab. Vor dem Image-Build laufen Python-Syntax, JavaScript-Syntax, `pytest` und ein Docker-Smoke-Build. Das veröffentlichte Image erhält außerdem Provenance-/SBOM-Metadaten.
