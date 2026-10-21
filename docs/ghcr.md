# GitHub Container Registry

Der Workflow `.github/workflows/ghcr.yml` baut Images für `linux/amd64` und `linux/arm64` und veröffentlicht sie unter:

```text
ghcr.io/domhit/smarttube-partyqueue
```

## Tags

- Push auf `develop`: `develop` und `sha-<commit>`
- Git-Tag `v3.0.0`: `v3.0.0`, `3.0.0`, `3.0` und `latest`
- Vorabversionen: beispielsweise `v3.1.0-beta1` und `3.1.0-beta1`

## Pull

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:3.0.0
```

Für den aktuellen stabilen Release:

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:latest
```

## Veröffentlichung

```bash
git tag -a v3.0.0 -m "SmartTube PartyQueue 3.0.0"
git push origin v3.0.0
```

Der Tag löst den Workflow aus. Das Paket muss auf GitHub auf `Public` stehen, wenn anonyme Pulls erlaubt sein sollen.

## Portainer und Compose

`docker-compose.ghcr.yml` ist für diesen Release auf `3.0.0` festgesetzt. Wer automatisch dem neuesten stabilen Release folgen möchte, kann den Tag auf `latest` ändern.
