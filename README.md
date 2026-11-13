# mini-rag-python

Portage en Python d'un mini-RAG (questions/réponses sur documents PDF avec citations), puis évolution vers un service LLM de production et un agent à outils. Projet d'apprentissage, très documenté.

> État : socle posé (Story 00). Le RAG n'est pas encore porté ; voir la feuille de route.

## Démarrer
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
Si `pytest` affiche des tests verts, l'environnement est prêt.

## Documentation
| Document | Contenu |
|---|---|
| [Feuille de route](docs/feuille-de-route.md) | Phases, stories, ce qu'on peut revendiquer après chacune |
| [Suivi des stories](docs/suivi-stories.md) | Statut détaillé de chaque story |
| [Fondamentaux de Python](docs/python/01-fondamentaux.md) | Ce qu'il faut savoir lire, comparé à PHP/JS |
| [Carte de l'écosystème](docs/python/02-ecosysteme.md) | Quel outil fait quoi et quand le choisir |
| [Erreurs et débogage](docs/python/03-erreurs-et-debogage.md) | Lire une trace, hypothèse avant correction |
| [Journal](docs/journal.md) | Séances et bugs corrigés à la main |

## Structure
```
src/mini_rag/     le code
tests/            les tests (pytest)
eval/             questions d'évaluation (comparées à la version TypeScript)
docs/             la documentation
```

## Confidentialité
`data/`, `index/` et `.env` ne sont jamais commités. Les corpus de test sont fictifs ou libres de droits.
