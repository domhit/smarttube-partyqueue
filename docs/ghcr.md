# GitHub Container Registry

Der Workflow `.github/workflows/ghcr.yml` baut Images für `linux/amd64` und `linux/arm64` und veröffentlicht sie unter:

```text
ghcr.io/domhit/smarttube-partyqueue
```

## Tags

- Push auf `develop`: `develop` und `sha-<commit>`
- Git-Tag `v4.3.0-alpha1`: `v4.3.0-alpha1`, `4.3.0-alpha1`, `3.0` und `latest`
- Vorabversionen: beispielsweise `v4.3.0-alpha1-beta1` und `4.3.0-alpha1-beta1`

## Pull

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:4.3.0-alpha1
```

Für den aktuellen stabilen Release:

```bash
docker pull ghcr.io/domhit/smarttube-partyqueue:latest
```

## Veröffentlichung

```bash
git tag -a v4.3.0-alpha1 -m "SmartTube PartyQueue 4.3.0-alpha1"
git push origin v4.3.0-alpha1
```

Der Tag löst den Workflow aus. Das Paket muss auf GitHub auf `Public` stehen, wenn anonyme Pulls erlaubt sein sollen.

## Portainer und Compose

`docker-compose.ghcr.yml` ist für diesen Release auf `4.3.0-alpha1` festgesetzt. Wer automatisch dem neuesten stabilen Release folgen möchte, kann den Tag auf `latest` ändern.
