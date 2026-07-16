# AGENTS.md — GestSIS_Alarm

Service Django + Django REST Framework qui gère les alarmes de GestSIS : récupération de mails, extraction des données des rapports de mobilisation (PDF), et API d'administration. Les dépendances sont gérées avec **`uv`**.

> Dans l'environnement de dev intégré [GestSIS_dev_docker](../AGENTS.md), ce service tourne dans le conteneur `gestsis-alarm` (port 8002) et **les commandes s'exécutent via Docker Compose**, ex. `docker compose exec alarm uv run manage.py test`. Les commandes ci-dessous sont données depuis la racine du dépôt (utiles en standalone, et à préfixer par `docker compose exec alarm` dans l'env intégré).

Versions exactes (Python, Django, DRF…) : voir `pyproject.toml` — c'est la source de vérité (le `README.md` peut être en retard).

## Structure

- `gestsis_alarm/` — projet Django (settings, urls, wsgi)
- `admin_panel/` — API de la vue d'administration (models, serializers, views, permissions)
- `mail_parser/` — récupération des mails et parsing des PDF ; les tests vivent dans son dossier `tests`
- `manage.py`, `_scripts/init.py` (génère `.env` + clé secrète Django), `storage/` (PDF)

## Commandes (`uv`)

```bash
uv sync                          # installer les dépendances (--locked en CI/Docker)
uv run _scripts/init.py [-f]     # créer .env + GESTSIS_ALARM_SECRET_KEY (-f force une nouvelle clé)
uv run manage.py migrate         # migrations
uv run manage.py loaddata sis    # données initiales
uv run manage.py runserver       # serveur de dev (0.0.0.0:8002 dans Docker)
uv run manage.py test            # tests unitaires
```

## Commandes de gestion métier

Exécutables sans serveur web (voir `--help` pour les options) :

- `retrieve_mail` — télécharge les PDF de rapports depuis le serveur mail
- `extract_pdf <fichier>` — extrait les données d'un rapport PDF
- `mail_and_extract` — combine les deux (destiné au cron ; enregistre en base)
- `diagnose_pdf_parsing` — teste le parsing sans rien écrire en base (diagnostic)

## Configuration

`.env` (django-environ), généré par `_scripts/init.py`. Variables clés : `GESTSIS_ALARM_SECRET_KEY` (auto), `GESTSIS_DATABASE_URL` (SQLite par défaut ; MySQL/PostgreSQL/Oracle supportés), `GESTSIS_ALARM_MAIL_*` (paramètres mail des commandes ci-dessus). Les JWT émis par le service Auth sont vérifiés avec la clé publique `storage/keys/auth-public.key` (fournie par `init.sh` dans l'env intégré).

## Conventions

- PEP 8.
- Tout changement doit être couvert par un test (`uv run manage.py test`).
