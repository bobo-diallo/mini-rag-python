# Structure d'un projet Python : conventions à respecter

Aide-mémoire pour juger, et construire, la structure d'un projet Python. Les conventions viennent surtout de la documentation de packaging officielle (PyPA), de PEP 8 (style) et de PEP 257 (docstrings). Un **PEP** (*Python Enhancement Proposal*) est un document de référence de la communauté Python, un peu comme une RFC.

## 1. L'arborescence de base

```
mon-projet/
├── pyproject.toml        # déclare le projet, ses dépendances, la config des outils
├── README.md
├── .gitignore
├── src/
│   └── mon_paquet/       # le code, dans un paquet importable
│       ├── __init__.py
│       └── ...
├── tests/                # les tests, hors du code livré, en miroir de src/
└── docs/
```

| Élément | Rôle | Analogie |
|---|---|---|
| `pyproject.toml` | Un seul fichier pour le nom, la version, les dépendances et la config de `pytest`, `ruff`, `mypy` | `composer.json` (PHP), `pom.xml` (Java) |
| Disposition `src/` | Le code est dans `src/mon_paquet/`, pas à la racine. On est ainsi **obligé** d'importer le paquet installé, et non le dossier courant par accident. | Séparer `src/main` de `src/test` en Java |
| Paquet | Un dossier contenant un `__init__.py` : Python peut l'importer (`import mon_paquet`). | un `namespace` PHP ou un `package` Java |
| `tests/` | Séparé du code, avec la même arborescence que `src/`. | `src/test/java` |

## 2. Le rôle de `__init__.py`

Un fichier `__init__.py` dans un dossier dit à Python « ce dossier est un paquet ». Il peut rester **vide**. On y met parfois la liste de ce que le paquet rend public. En règle : à garder minimal, sans traitement lourd.

## 3. Nommage (PEP 8)

| Quoi | Convention | Exemple |
|---|---|---|
| Fichiers (modules) et dossiers (paquets) | `snake_case`, courts, minuscules | `pdf_loader.py` |
| Fonctions et variables | `snake_case` | `chunk_pages` |
| Classes | `PascalCase` | `PageText` |
| Constantes | `MAJUSCULES_AVEC_TIRETS_BAS` | `DEFAULT_CHUNK_SIZE` |
| Interne à un module | préfixe `_` | `_split_text` |

## 4. Qualité de code attendue

- **Annotations de types** : `def chunk(pages: list[PageText]) -> list[Chunk]`. Python ne les impose pas à l'exécution, mais elles documentent et un outil (`mypy`, `pyright`) les vérifie.
- **Docstrings** : une phrase entre `"""` en tête de chaque module, classe et fonction publique.
- **Pas de code qui s'exécute à l'import** : importer un fichier ne doit pas lancer un traitement. Les points d'entrée vont soit derrière `if __name__ == "__main__":`, soit dans `[project.scripts]` du `pyproject.toml`.
- **Style automatique** : `ruff` formate et signale les erreurs bêtes. Analogie : PHP-CS-Fixer, ou Checkstyle.

## 5. Organiser par domaine, pas par type technique

On regroupe le code par ce qu'il fait (`ingestion/`, `retrieval/`, `generation/`), pas par catégories techniques (`models/`, `services/`, `utils/`). Cela rejoint le DDD : on retrouve le métier en lisant l'arborescence.

**Règle de dépendance** : `domain/` (les types et règles métier) ne dépend de **rien d'autre**. Tous les autres paquets peuvent en dépendre, jamais l'inverse. Ça évite les dépendances circulaires (A importe B qui importe A), qui sont fatales en Python.

## 6. Structure de ce projet

```
mini-rag-python/
├── pyproject.toml
├── src/mini_rag/
│   ├── __init__.py
│   ├── domain/            # Source, PageText, Chunk : types purs, sans dépendance
│   ├── ingestion/         # lire les PDF, découper en chunks
│   ├── cli.py             # commandes, déclarées dans [project.scripts]
│   └── (plus tard) retrieval/, generation/, api/, config.py
├── tests/                 # miroir de src/
│   └── fixtures/          # fichiers de test fixes (PDF fictifs)
├── eval/                  # questions d'évaluation et réponses attendues
└── docs/
```

**On ne crée un paquet que le jour où une story en a besoin** : pas de dossiers vides « au cas où ».

## 7. Pièges connus

- **Deux fichiers de test de même nom** dans des dossiers différents (`tests/a/test_x.py` et `tests/b/test_x.py`) peuvent se télescoper dans `pytest`. On l'évite avec un `__init__.py` dans les dossiers de tests ou l'option d'import `importlib`.
- **Dépendance circulaire** : voir règle de dépendance ci-dessus.
- **`__pycache__`, `.venv`, `.pytest_cache`** : générés, jamais commités (voir `.gitignore`).
