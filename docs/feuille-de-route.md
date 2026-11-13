# Feuille de route

Document vivant : mis à jour à la fin de chaque story. Chaque phase se termine par quelque chose qui marche et se démontre. **On ne revendique une compétence qu'après le projet qui la prouve.**

Niveau visé en Python : **lire et piloter** (lire n'importe quel code généré, connaître la carte de l'écosystème, structurer un projet, déboguer, écrire la petite colle). Pas la syntaxe récitée.

## Règles de travail
1. Une story = une étape vérifiable. Plan présenté et validé avant de coder.
2. TDD : le test avant le code. Un changement à la fois, mesure avant/après.
3. Aucun bloc de code généré n'est intégré sans pouvoir dire à voix haute ce qu'il fait et pourquoi.
4. Au moins un bug réel corrigé à la main par projet (hypothèse écrite avant d'appeler à l'aide), consigné dans `journal.md`.
5. La documentation avance avec le code : chaque story met à jour `docs/` (fondamentaux, carte de l'écosystème, glossaire du domaine).
6. Rythme visé : 3 séances de 45 à 60 minutes par semaine.

## Phases
| Phase | Contenu | Livrable | Ce qu'on peut alors dire |
|---|---|---|---|
| 0 | Socle : projet, environnement, tests, documentation de départ | `pytest` passe, docs de base | — |
| 1 | Portage du mini-RAG TypeScript : lecture PDF, découpage, embeddings, index SQLite, recherche, réponse avec citations, évaluation sur les mêmes questions | API `POST /ask` + scores comparés à la version TypeScript | « Python appliqué à un projet IA complet (API, tests, RAG) » |
| 2 | LLM en production : sorties structurées (JSON validé), prompts versionnés, reprises sur erreur, journal, coût par requête | service avec journal de coûts | « LLM en production : prompts versionnés, sorties structurées, traçabilité, maîtrise des coûts » |
| 3 | RAG évalué : découpage par structure comparé au découpage fixe, recherche hybride, reranking si le gain est mesuré, jeu de 25 à 30 questions | rapport d'évaluation d'une page | « RAG de bout en bout, évalué quantitativement, avec recherche hybride et citations » |
| 4 | Agents : agent à outils, approbation humaine, puis 2-3 agents orchestrés, garde-fous, journal d'audit | démonstration de 10 minutes | « Agents IA avec outils et approbation humaine, orchestration simple et traçable » |
| 5 | Déploiement : Docker, serveur, HTTPS, authentification, supervision, confidentialité | liens de démonstration stables | « Intégration et déploiement de solutions d'IA » |
| 6 | Preuves, en continu : README, schémas, rapport, vidéo, démonstration par projet | dépôt propre | — |

## Phase 1 : découpage prévu en stories (provisoire)
| Story | Contenu | Test de réussite |
|---|---|---|
| 00 | Socle et documentation de départ | `pytest` vert |
| 01 | Lecture de PDF page par page + découpage en chunks (1000/200) | mêmes nombres de chunks que la version TypeScript sur un même PDF fictif |
| 02 | Embeddings (`bge-m3` via Ollama) + recherche par le sens en mémoire | rang des bonnes pages sur les questions d'évaluation |
| 03 | Réponse avec citations vérifiées par le code + « je ne sais pas » | citations toutes présentes dans les extraits |
| 04 | Index persistant SQLite + sqlite-vec | résultats identiques avant/après persistance |
| 05 | API FastAPI `POST /ask` + configuration `.env` centralisée | tests d'API |
| 06 | Évaluation sur les mêmes questions, score comparé à TypeScript | tableau des scores des deux versions |

Les corpus de test sont **fictifs ou libres de droits** ; aucun document privé n'est lu par l'assistant ni commité.

## Tenu à jour ailleurs
- Détail et statut de chaque story : `docs/suivi-stories.md`.
- Section « Avancement » du `CLAUDE.md` : vue d'ensemble.
