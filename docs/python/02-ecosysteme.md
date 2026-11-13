# Carte de l'écosystème : quel outil fait quoi, et quand le choisir

À tenir à jour à chaque nouvelle bibliothèque introduite (règle du projet). La colonne « Équivalent TypeScript » renvoie au projet `mini-rag-local`.

| Besoin | Outil Python | Équivalent TypeScript | Phase | Quand le choisir |
|---|---|---|---|---|
| Isoler les dépendances | `venv` (livré avec Python) | `node_modules` | 1 | toujours, un par projet |
| Installer des paquets | `pip` | `npm` | 1 | par défaut ; `uv` est une alternative plus rapide, à voir plus tard |
| Déclarer le projet | `pyproject.toml` | `package.json` | 1 | toujours |
| Tests | `pytest` | Vitest | 1 | toujours : fonctions `test_*`, `assert` simple |
| API HTTP | `FastAPI` + `uvicorn` | Node `http` (serveur maison) | 1 | exposer `POST /ask` ; documentation auto sur `/docs` |
| Validation de données | `pydantic` | Zod / interfaces | 1 | schémas d'entrée/sortie, JSON de modèle à valider |
| Réglages depuis `.env` | `pydantic-settings` | `config.ts` + `.env` | 1 | une seule classe de configuration centralisée |
| Lecture de PDF | `pypdf` | `pdf-parse` | 1 | extraire le texte page par page |
| Découpage de texte | fonction maison ou `langchain-text-splitters` | LangChain.js | 1 | maison d'abord (on comprend), bibliothèque ensuite si utile |
| Embeddings et modèle local | client `ollama` ou HTTP avec `httpx` | `@langchain/ollama` | 1 | `bge-m3` et un modèle ~3B comme dans l'autre projet |
| Base d'index | `sqlite3` (livré avec Python) + `sqlite-vec` | `better-sqlite3` + sqlite-vec | 1 | même choix que le projet TypeScript : un seul fichier |
| Appels HTTP | `httpx` | `fetch` | 1-2 | synchrone ou asynchrone avec la même API |
| API Claude | SDK `anthropic` | `@anthropic-ai/sdk` | 2 | modèle `claude-haiku-5-5` par défaut |
| Journalisation | module `logging` | `console` + fichier jsonl | 2 | jamais `print` en dehors du débogage |
| Typage statique | `mypy` ou `pyright` | `tsc` | 2 | vérifier les annotations, optionnel mais recommandé |
| Style et erreurs bêtes | `ruff` | ESLint + Prettier | 2 | un seul outil rapide pour lint et format |
| Agents et outils | boucle maison, puis éventuellement `langgraph` | — | 4 | maison d'abord pour comprendre la boucle |
| Conteneur | Docker | Docker | 5 | emballage et déploiement |

## Règles de choix
- **Maison d'abord, bibliothèque ensuite**, pour tout ce qui est au cœur de l'apprentissage (découpage, recherche, boucle d'agent) : on comprend, puis on remplace si la bibliothèque apporte un vrai gain mesuré.
- **Chaque dépendance ajoutée est justifiée** dans ce tableau (rôle, alternative écartée).
- **Python 3.12** pour ce projet (la 3.15 est installée sur la machine, mais les bibliothèques d'IA suivent la 3.12 de plus près).
- Les versions exactes sont figées dans `pyproject.toml` lors de la première installation réelle ; aucune version n'est inventée ici.
