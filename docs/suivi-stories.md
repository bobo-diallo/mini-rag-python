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
- **Branche :** `story/01-pdf-loading-and-chunking`
- **PR :** [#2](https://github.com/bobo-diallo/mini-rag-python/pull/2), fusionnée le 2026-11-14
- **Statut :** ✅ terminée
- **Test de réussite :** même nombre de chunks que la version TypeScript sur un même PDF fictif

- [x] Conventions de structure d'un projet Python : `docs/python/05-structure-projet.md`
- [x] Types du domaine (`Source`, `PageText`, `Chunk`) dans `mini_rag/domain/`
- [x] Découpeur maison récursif (taille 1000, chevauchement 200, un chunk ne franchit pas une page)
- [x] Comparaison avec `langchain-text-splitters` (référence de test uniquement) : mêmes extraits sur 6 textes × 4 réglages
- [x] Lecteur PDF (`pypdf`) testé sur un PDF fictif (copié du projet TypeScript, texte fictif vérifié)
- [x] Pipeline d'intégration continue (GitHub Actions) : `pytest` à chaque PR vers `main` et à chaque mise à jour de `main`
- [x] Commande de comptage `mini-rag-chunks` (`[project.scripts]`)
- [x] **Test de réussite atteint** : sur `tests/fixtures/fictional-report.pdf` (6 pages, généré par `scripts/generate_fictional_pdf.py`), Python et TypeScript donnent les mêmes résultats : 29 chunks, taille moyenne 877, min 354, max 999
- [x] Glossaire et carte de l'écosystème mis à jour
- [x] Mise en conformité avec la règle « tout en anglais sauf les commentaires » (branche, fichiers, noms de tests et de variables)

## Story 02 — Embeddings et recherche par le sens
- **Branche :** `story/02-embeddings-and-search`
- **PR :** [#3](https://github.com/bobo-diallo/mini-rag-python/pull/3), fusionnée le 2026-11-16
- **Statut :** ✅ terminée
- **Test de réussite :** rang des bonnes pages sur les questions d'évaluation (hit@3 et MRR mesurés avec `bge-m3`, corpus fictif)

- [x] `cosine_similarity` (vecteurs proches, opposés, dimensions différentes, vecteur nul)
- [x] `InMemoryVectorStore` : ajouter, chercher les `k` plus proches, trié du meilleur au moins bon
- [x] Interface `Embedder` et traitement par lots (faux embedder pour les tests)
- [x] `OllamaEmbedder` (`httpx`), testé sans réseau, plus un test d'intégration sauté si Ollama est absent
- [x] Étape 4b : contrat `Embedder` obligatoire (`@abstractmethod`, déclaré par `OllamaEmbedder`) et configuration centralisée (`Settings`, `.env.example`), valeurs d'adresse et de modèle retirées des classes
- [x] `Retriever` : indexer des chunks, chercher une question
- [x] Corpus fictif thématique « Guide client Astrolabe » (10 pages, `eval/corpus/`) et 12 questions (`eval/retrieval-questions.json`), figés ; 10 pages plutôt que 6 pour que le hasard ne donne que 30 % de hit@3 au lieu de 50 %
- [x] Commande de mesure `mini-rag-eval-retrieval` : rang de chaque question, hit@1, hit@3, MRR, référence du hasard. **Mesure 1 (`bge-m3`) : hit@3 = 100 %, MRR = 1,00** ; voir `docs/evaluations.md` (corpus trop facile pour départager des modèles)
- [x] Glossaire (dimension, licence, hit@k, MRR, interface…), carte de l'écosystème, suivi

## Story 03 — Réponse avec citations vérifiées
- **Branche :** `story/03-answers-with-citations`
- **PR :** — (sur `/push`)
- **Statut :** 🔄 en cours (plan validé)
- **Test de réussite :** citations toutes présentes dans les extraits fournis, et « je ne sais pas » quand les documents ne contiennent pas la réponse (mesuré avec `llama3.2:3b`)

- [x] a. `resolve_citations` : relier les « [n] » de la réponse aux extraits réels, signaler les numéros inventés
- [x] b. `build_prompt`, `NO_ANSWER`, estimation des tokens
- [x] c. `OllamaChatModel` (`httpx`, température 0), testé sans réseau puis contre le vrai `llama3.2:3b`
- [x] c2. Génération à distance : `AnthropicChatModel` (Claude Haiku 5.5, SDK `anthropic`), choix par `CHAT_PROVIDER`, clé dans `SecretStr` lue depuis `.env`, échec avant tout calcul si la clé manque ; `pytest` n'appelle plus Ollama par défaut. **Pas encore testé contre le vrai service (clé d'API à créer)**
- [x] d. `Answerer` : seuil de refus sans appeler le modèle, « je ne sais pas » reconnu, extraits retirés si le prompt déborde
- [x] e. Réglages dans `Settings` et `.env.example` (modèle, `num_ctx`, nombre d'extraits, seuil)
- [x] f. Commande `mini-rag-ask`
- [ ] g. Mesure : 12 questions du guide + 4 hors sujet (`eval/out-of-scope-questions.json`), prédiction écrite avant. **Mesure 2 faite (1 passage)** : 0 citation inventée, 0 réponse inventée hors sujet, mais 5/12 refus à tort par le modèle ; voir `docs/evaluations.md`. Reste : 3 passages, variante de prompt avec exemple, calibration du seuil
- [ ] h. Glossaire, carte de l'écosystème, suivi

