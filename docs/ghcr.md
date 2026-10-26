# GHCR Deployment

Das produktive Image wird über GitHub Container Registry bereitgestellt:

```text
ghcr.io/domhit/smarttube-partyqueue
```

## Empfohlener Release

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:4.4.2
```

Für Installationen, die automatisch dem jeweils aktuellen stabilen Release folgen sollen:

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:latest
```

## Release-Tags

Für einen stabilen V4.4.2-Release:

```bash
git tag -a v4.4.2 -m "SmartTube PartyQueue 4.4.2"
git push origin v4.4.2
```

Die Release-Pipeline soll mindestens `v4.4.2`, `4.4.2`, `4.4` und `latest` veröffentlichen.

## Compose

`docker-compose.ghcr.yml` ist auf `4.4.2` festgesetzt. Wer bewusst einer Entwicklungs- oder Vorabversion folgen möchte, ändert den Image-Tag explizit.

Persistente Volumes:

```yaml
volumes:
  - ./data:/app/data
  - ./adb:/root/.android
```

`adb` enthält private ADB-Schlüssel und gehört nicht ins Repository.
