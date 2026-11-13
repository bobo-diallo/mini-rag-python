# mini-rag-python

## Description
Portage en Python du projet `mini-rag-local` (TypeScript, dossier voisin), puis évolution vers un service LLM de production et un agent à outils. **Projet d'apprentissage documenté** : l'objectif est de savoir lire et piloter Python et l'écosystème IA, pas de réciter la syntaxe. Destiné à être publié sur GitHub (aucun document privé, aucun plan de carrière dans le dépôt).

## Stack technique (cible)
- Python 3.12, `venv`, `pip`, `pyproject.toml`
- Tests : `pytest` ; API : FastAPI + pydantic ; index : SQLite + sqlite-vec ; Ollama en local (`bge-m3`, modèle ~3B) ; Claude (`claude-haiku-5-5`) en option, uniquement sur des extraits publics
- Détail et justification de chaque outil : `docs/python/02-ecosysteme.md`

## Conventions
- Communication et documentation en français ; identifiants techniques en anglais.
- DDD / TDD / SOLID ; le test avant le code ; un changement à la fois, mesure avant/après.
- **Documentation avec le code** : chaque story met à jour `docs/` (fondamentaux, carte de l'écosystème, suivi, feuille de route).
- Aucun bloc généré n'est accepté sans pouvoir l'expliquer ; un bug corrigé à la main par projet (`docs/journal.md`).
- Git : `main` seule branche longue ; une branche par story `story/<nn>-<résumé>` créée avant de modifier ; commits libres, message préfixé `<branche>: ` ; **jamais de ligne Co-Authored-By** ; push, PR et fusion seulement sur `/push`.
- `data/`, `index/`, `.env`, `docs/prive/` ne sont jamais commités. Ne jamais lire de documents privés avec les outils de l'assistant. Ne jamais fabriquer de données.
- **Pédagogie** : l'utilisateur est développeur web (PHP, Java) et découvre l'écosystème IA. Tout terme nouveau (training, MCP, embedding...) est expliqué simplement à sa première apparition, avec une analogie web si utile, puis ajouté à `docs/python/04-glossaire.md`. On n'est pas pressé.
- Toujours activer l'environnement avant de travailler : `source .venv/bin/activate`.

## Avancement
- [x] Story 00 : socle, tests, documentation de départ
- [ ] Phase 1 : portage du mini-RAG (stories 01 à 06, détail dans `docs/feuille-de-route.md`)
- [x] Story 00b : feuille de route étendue + glossaire (en cours, PR sur `/push`)
- [ ] Phase 2b : Hugging Face et modèles ouverts
- [ ] Phase 2 : LLM en production
- [ ] Phase 3 : RAG évalué
- [ ] Phase 3b : documents et vision (factures synthétiques)
- [ ] Phase 3c : adapter un modèle (LoRA) et arbre de décision
- [ ] Phase 4 : agents (dont MCP)
- [ ] Phase 5 : déploiement, observabilité, sécurité
- [ ] Phase 6 : preuves et récit
- [ ] Phase 7 : métier de consultant (grille d'audit, 3 cas fictifs)

## Documentation
`docs/feuille-de-route.md` · `docs/suivi-stories.md` · `docs/journal.md` · `docs/python/01-fondamentaux.md` · `docs/python/02-ecosysteme.md` · `docs/python/03-erreurs-et-debogage.md` · `docs/python/04-glossaire.md`
