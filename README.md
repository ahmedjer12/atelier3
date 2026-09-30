# Projet DevOps ESIEA

Projet réalisé dans le cadre de l'évaluation DevOps.

L'objectif est de mettre en place une chaîne DevOps complète allant du code source jusqu'au déploiement d'une image Docker, avec :

- conteneurisation Docker ;
- Docker Compose ;
- tests automatisés ;
- lint ;
- CI avec GitHub Actions ;
- CD avec GitHub Actions ;
- GitHub Container Registry (GHCR) ;
- déploiement sur un self-hosted runner ;
- healthcheck et rollback ;
- métriques Prometheus ;
- règles d'alerte Prometheus.

---

## 1. Architecture

L'application est une API Flask utilisant Redis.

Architecture locale :

Client
  |
  v
Nginx :5000
  |
  v
Flask / Gunicorn
  |
  v
Redis

Les services principaux sont :
- app-blue : instance Flask du profil blue ;
- app-green : instance Flask du profil green ;
- redis : stockage utilisé par l'application ;
- nginx : reverse proxy exposé sur le port 5000.
2. Technologies utilisées
- Python 3.11 / 3.12
- Flask
- Redis
- Gunicorn
- Docker
- Docker Compose
- Nginx
- Pytest
- Flake8
- Pytest Coverage
- GitHub Actions
- GitHub Container Registry
- Prometheus Client
3. Structure du projet
atelier3/
|
|-- .github/
|   |-- actions/
|   |   `-- setup-python/
|   |       `-- action.yml
|   |
|   `-- workflows/
|       |-- ci.yml
|       `-- cd.yml
|
|-- nginx/
|   `-- default.conf
|
|-- prometheus/
|   `-- alerts.yml
|
|-- app.py
|-- test_app.py
|-- requirements.txt
|-- Dockerfile
|-- Dockerfile.naive
|-- docker-compose.yml
|-- .dockerignore
|-- .flake8
`-- README.md

4. Installation
Cloner le dépôt :
git clone https://github.com/ahmedjer12/atelier3.git
cd atelier3

Installer les dépendances Python :
python -m pip install -r requirements.txt

5. Lancement local avec Docker Compose
Pour lancer l'environnement green :
docker compose --profile green up -d --build

Vérifier les conteneurs :
docker compose --profile green ps

L'application est accessible sur :
http://localhost:5000

Pour arrêter les conteneurs :
docker compose --profile green down

6. Endpoints de l'application
Healthcheck
GET /health

Exemple :
curl http://localhost:5000/health

Réponse attendue :
{
  "redis": "ok",
  "status": "ok"
}

Status
GET /status

Expose notamment :
- la version ;
- le SHA déployé ;
- la couleur de déploiement.
Visits
GET /visits

Cet endpoint utilise réellement Redis pour incrémenter un compteur.
Metrics
GET /metrics

Exemple :
curl http://localhost:5000/metrics

7. Tests
Lancer les tests :
python -m pytest -v

Les tests couvrent notamment :
- fonctions applicatives ;
- endpoint /health ;
- comportement en cas d'indisponibilité Redis ;
- endpoint /status ;
- endpoint /metrics ;
- interaction réelle avec Redis via /visits.
8. Lint
Lancer Flake8 :
python -m flake8 app.py test_app.py

9. Docker
Le Dockerfile utilise un build multi-stage.
Principales caractéristiques :
- image Python versionnée ;
- runtime basé sur python:3.12-slim ;
- utilisateur non-root appuser ;
- HEALTHCHECK sur /health ;
- exécution avec Gunicorn ;
- .dockerignore.
Construire l'image manuellement :
docker build -t atelier3-app .

10. Continuous Integration
Le workflow CI se trouve dans :
.github/workflows/ci.yml

La CI est exécutée lors :
- des Pull Requests ;
- des push sur main.
Elle contient quatre jobs principaux :
lint
test
build
ci-ok

Matrix de tests
Les tests sont exécutés sur :
Python 3.11
Python 3.12

Redis dans la CI
Le job de test démarre un service Redis réel.
Le test /visits utilise ce service afin de vérifier une interaction réelle avec Redis.
Cache
Les dépendances Python utilisent le cache intégré de actions/setup-python.
Artifacts
Les tests génèrent :
coverage.xml
junit.xml

Ces fichiers sont publiés comme artifacts GitHub Actions.
Action locale réutilisable
L'action :
.github/actions/setup-python/action.yml

centralise :
- la configuration Python ;
- le cache des dépendances ;
- l'installation de requirements.txt.
11. Continuous Deployment
Le workflow CD se trouve dans :
.github/workflows/cd.yml

Le CD démarre après une CI réussie sur main.
Il peut également être lancé manuellement avec :
workflow_dispatch

et l'environnement :
production

12. GitHub Container Registry
Les images sont publiées sur :
ghcr.io/ahmedjer12/atelier3

Trois tags sont générés :
latest
SHA court du commit
1.0.0

Exemple :
ghcr.io/ahmedjer12/atelier3:latest
ghcr.io/ahmedjer12/atelier3:7cd5e62
ghcr.io/ahmedjer12/atelier3:1.0.0

Le workflow utilise GITHUB_TOKEN avec des permissions explicites :
permissions:
  contents: read
  packages: write

13. Déploiement
Le déploiement est exécuté sur un GitHub Actions self-hosted runner installé sur une machine Windows.
Le job de déploiement :
1. récupère l'image depuis GHCR ;
2. définit la version et le SHA ;
3. démarre les services avec Docker Compose ;
4. vérifie /health ;
5. enregistre le SHA déployé si le déploiement réussit.
Le déploiement utilise :
docker compose --profile green up -d --pull always

14. Healthcheck post-déploiement
Après le déploiement, le workflow teste :
http://localhost:5000/health

Un maximum de trois tentatives est effectué.
En cas de succès, le SHA courant est enregistré comme version fonctionnelle.
15. Rollback
Le dernier SHA fonctionnel est stocké sur le runner dans :
C:\actions-runner\deploy-state\previous_sha.txt

Si le healthcheck échoue après les trois tentatives :
1. le workflow récupère le SHA précédent ;
2. télécharge l'image correspondante ;
3. redéploie cette image ;
4. termine le job en erreur afin d'indiquer que le nouveau déploiement a échoué.
16. Métriques Prometheus
L'application expose des métriques sur :
/metrics

Compteur de requêtes
http_requests_total

Labels :
endpoint
code

Exemple :
http_requests_total{code="200",endpoint="/health"}

Histogramme de latence
http_request_duration_seconds

Il permet de calculer des percentiles tels que :
- p95 ;
- p99.
Informations de déploiement
app_deployment_info

Expose notamment :
version
sha

17. Alertes Prometheus
Les règles sont définies dans :
prometheus/alerts.yml

High5xxErrorRate
Déclenchée lorsque le taux de réponses HTTP 5xx dépasse :
5 %

pendant :
5 minutes

Ce seuil permet de détecter une dégradation persistante tout en évitant de déclencher une alerte sur une erreur ponctuelle.
HighRequestLatencyP95
Déclenchée lorsque la latence p95 dépasse :
500 ms

pendant :
5 minutes

Cette règle permet de détecter une dégradation durable des performances de l'application.
18. Vérifications principales
python -m pytest -v
python -m flake8 app.py test_app.py
docker compose --profile green config
docker compose --profile green up -d --build
curl http://localhost:5000/health
curl http://localhost:5000/metrics

19. Repository
GitHub :
https://github.com/ahmedjer12/atelier3


Ensuite dans le terminal :


git add README.md
git commit -m "docs: finalize project README"
git push