# GitHub Container Registry

Der Workflow `.github/workflows/ghcr.yml` testet und baut Images fÃ¼r `linux/amd64` und `linux/arm64` und verÃ¶ffentlicht sie unter `ghcr.io/domhit/smarttube-partyqueue`.

## Entwicklungsimages

Pushes auf `develop` oder `develop-v*` erzeugen den jeweiligen Branch-Tag sowie einen `sha-*`-Tag. Der aktuell verwendete Entwicklungsbranch ist `develop-v4`.

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:develop-v4
```

## Release Candidate

Der V4.5 Release Candidate wird mit folgendem Git-Tag verÃ¶ffentlicht:

```bash
git tag -a v4.5.0 -m "SmartTube PartyQueue v4.5.0"
git push origin v4.5.0
```

Danach ist das versionierte Image verfÃ¼gbar als:

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:4.5.0
```

`docker-compose.ghcr.yml` ist fÃ¼r den RC bewusst auf `4.5.0` festgesetzt. Erst der finale, nach `main` gemergte `v4.5.0`-Release soll als stabiler Produktionsstand dokumentiert werden.

## CI-PrÃ¼fungen vor VerÃ¶ffentlichung

Der GHCR-Workflow hÃ¤ngt vom wiederverwendbaren Testworkflow ab. Vor dem Image-Build laufen Python-Syntax, JavaScript-Syntax, `pytest` und ein Docker-Smoke-Build. Das verÃ¶ffentlichte Image erhÃ¤lt auÃŸerdem Provenance-/SBOM-Metadaten.
