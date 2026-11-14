# Suivi des stories

Une section par story : branche, PR, statut (✅ terminée, 🔄 en cours, 📋 prévue), checklist. Le plan d'ensemble est dans `docs/feuille-de-route.md`.

## Story 00 — Socle et documentation de départ
- **Branche :** commit initial sur `main` (seul commit autorisé directement sur `main`)
- **PR :** —
- **Statut :** ✅ terminée

- [x] Dossier, `git init`, `.gitignore` (environnement, données, documents personnels)
- [x] `pyproject.toml`, paquet `src/mini_rag`, tests `pytest`
- [x] Documentation : fondamentaux Python, carte de l'écosystème, erreurs et débogage
- [x] Feuille de route, suivi, journal, `CLAUDE.md`, README

## Story 00b — Feuille de route étendue et glossaire
- **Branche :** `story/00b-feuille-de-route-et-glossaire`
- **PR :** [#1](https://github.com/bobo-diallo/mini-rag-python/pull/1), fusionnée le 2026-11-13
- **Statut :** ✅ terminée

- [x] Feuille de route étendue (phases 2b, 3b, 3c, 7) validée
- [x] Glossaire `docs/python/04-glossaire.md` (jargon expliqué pour un développeur web)
- [x] Règle de pédagogie ajoutée à la feuille de route et au `CLAUDE.md`
- [x] Lignes HF, vision, `peft`, MCP, observabilité dans `02-ecosysteme.md`

## Story 01 — Lecture de PDF et découpage
- **Branche :** `story/01-lecture-pdf-et-decoupage`
- **PR :** — (sur `/push`)
- **Statut :** 🔄 en cours (plan validé)
- **Test de réussite :** même nombre de chunks que la version TypeScript sur un même PDF fictif

- [x] Conventions de structure d'un projet Python : `docs/python/05-structure-projet.md`
- [x] Types du domaine (`Source`, `PageText`, `Chunk`) dans `mini_rag/domain/`
- [x] Découpeur maison récursif (taille 1000, chevauchement 200, un chunk ne franchit pas une page)
- [x] Comparaison avec `langchain-text-splitters` (référence de test uniquement) : mêmes extraits sur 6 textes × 4 réglages
- [x] Lecteur PDF (`pypdf`) testé sur un PDF fictif (copié du projet TypeScript, texte fictif vérifié)
- [x] Pipeline d'intégration continue (GitHub Actions) : `pytest` à chaque PR vers `main` et à chaque mise à jour de `main`
- [x] Commande de comptage `mini-rag-chunks` (`[project.scripts]`)
- [x] **Test de réussite atteint** : sur `tests/fixtures/rapport-fictif.pdf` (6 pages, généré par `scripts/generer_pdf_fictif.py`), Python et TypeScript donnent les mêmes résultats : 29 chunks, taille moyenne 877, min 354, max 999
- [x] Glossaire et carte de l'écosystème mis à jour
- [ ] Mise en conformité avec la règle « tout en anglais sauf les commentaires » (branche, noms de tests et de variables)
