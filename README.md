# Atelier 3 - Conteneurisation Docker

## Application

Application Flask conteneurisee avec Docker, Gunicorn et Redis.

Endpoints disponibles :

- `/health` : verification de l'etat de l'application
- `/status` : informations sur le service
- `/visits` : compteur de visites persistant dans Redis

## Build de l'image

Construire l'image Docker multi-stage :

```bash
docker build -t atelier3-web .
```

## Lancer la stack complete

```bash
docker compose up -d --build
```

Verifier les services :

```bash
docker compose ps
```

Arreter la stack :

```bash
docker compose down
```

## Tests

Tester l'application :

```bash
curl http://localhost:5000/health
```

Resultat attendu :

```json
{"status":"ok"}
```

Tester le compteur Redis :

```bash
curl http://localhost:5000/visits
```

## Utilisateur non-root

Verifier l'utilisateur du conteneur web :

```bash
docker compose exec web whoami
```

Resultat attendu :

```text
appuser
```

## Comparaison des images Docker

| Image | Disk usage | Content size |
|---|---:|---:|
| Image naive | 1.65 GB | 423 MB |
| Image multi-stage | 231 MB | 55.6 MB |

Le build multi-stage avec `python:3.12-slim` permet une reduction d'environ **86 %** de la taille de l'image.

## Docker Compose

La stack contient deux services :

- `web` : application Flask executee avec Gunicorn
- `redis` : stockage persistant du compteur de visites

Les services communiquent via un reseau Docker dedie.

Les donnees Redis sont conservees dans un volume nomme `redis-data`.

Le service `web` attend que Redis soit `healthy` avant de demarrer.

## Registry Docker Hub

Image publiee :

```text
ahmedjer123/atelier3
```

Tags :

```text
ahmedjer123/atelier3:1.0.0
ahmedjer123/atelier3:latest
```

Telecharger l'image :

```bash
docker pull ahmedjer123/atelier3:1.0.0
```