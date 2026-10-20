## GitHub Container Registry

Die GitHub-Actions-Workflowdatei `.github/workflows/ghcr.yml` baut und veröffentlicht das Container-Image automatisch in der GitHub Container Registry.

### Veröffentlichte Tags

- Push auf `develop`: `develop` und `sha-<commit>`
- Git-Tag `v3.0.0-beta2`: `v3.0.0-beta2`, `3.0.0-beta2` und `sha-<commit>`
- Stabile Tags wie `v3.0.0`: zusätzlich `3.0` und gemäß Docker Metadata Action `latest`

Das Image wird für `linux/amd64` und `linux/arm64` gebaut.

### Einrichtung im GitHub-Repository

1. Repository unter **Settings → Actions → General → Workflow permissions** öffnen.
2. **Read and write permissions** aktivieren, falls die Organisation die `GITHUB_TOKEN`-Berechtigungen nicht über die Workflowdatei zulässt.
3. Änderungen auf `develop` pushen oder einen Release-Tag veröffentlichen.
4. Unter **Actions** den Workflow `Build and publish container image` kontrollieren.
5. Unter **Packages** das Paket `smarttube-partyqueue` öffnen und die Sichtbarkeit auf `Public` setzen, wenn anonyme Pulls gewünscht sind.

Es ist kein persönlicher Zugriffstoken für die Veröffentlichung aus GitHub Actions erforderlich. Der Workflow nutzt `GITHUB_TOKEN` mit `packages: write`.

### Image lokal testen

`GITHUB-OWNER` durch den kleingeschriebenen GitHub-Benutzer- oder Organisationsnamen ersetzen:

```bash
docker pull ghcr.io/GITHUB-OWNER/smarttube-partyqueue:3.0.0-beta2
docker run --rm ghcr.io/GITHUB-OWNER/smarttube-partyqueue:3.0.0-beta2 python -c "import app.main; print(app.main.app.version)"
```

### Betrieb mit Docker Compose

```bash
cp docker-compose.ghcr.yml docker-compose.yml
sed -i 's/GITHUB-OWNER/dein-github-name/g' docker-compose.yml
docker compose pull
docker compose up -d
```

Die Verzeichnisse `./data` und `./adb` bleiben persistent. Das ADB-Verzeichnis enthält private Schlüssel und darf nicht veröffentlicht oder eingecheckt werden.

### Private Pakete

Für ein privates GHCR-Paket muss sich der Docker-Host vor dem Pull anmelden:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u GITHUB-BENUTZER --password-stdin
```

Der Token benötigt für Pulls mindestens `read:packages`.
