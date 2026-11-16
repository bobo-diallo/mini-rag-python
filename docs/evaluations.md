# Évaluations : les mesures, datées

Chaque mesure consigne les conditions, les résultats **tels qu'ils sont sortis**, et ce qu'on peut (et ne peut pas) en conclure. Règle : on ne modifie ni le corpus ni les questions pour améliorer un score ; on change le modèle ou le réglage, puis on remesure.

Commande : `mini-rag-eval-retrieval` (corpus `eval/corpus/`, questions `eval/retrieval-questions.json`).

## Mesure 1 — recherche par le sens, `bge-m3` (story 02)

**Conditions** : modèle `bge-m3` via Ollama 0.40.16, vecteurs de 1024 dimensions, similarité cosinus ; découpage 1000 / 200 (un chunk par page, donc rang d'un chunk = rang de sa page) ; corpus « Guide client Astrolabe » fictif de 10 pages ; 12 questions ; `k = 10`.

**Prédiction écrite avant la mesure** : « `bge-m3` trouve la bonne page en tête pour la plupart des questions, mais hésite sur les paires voisines (surtout remboursement contre litige, questions 7 et 8). »

**Résultats**

| # | Question (début) | Page attendue | Rang | Écart avec la 2e page | 2e page |
|---|---|---|---|---|---|
| 1 | Quelles sont les différentes offres… | 1 | 1 | 0,0363 | p4 |
| 2 | Quel jour de chaque mois… débité ? | 2 | 1 | **0,0006** | p7 |
| 3 | …carte prépayée… | 2 | 1 | 0,1259 | p7 |
| 4 | …télécharger le récapitulatif… | 3 | 1 | 0,0590 | p7 |
| 5 | …mettre mon service en pause… | 4 | 1 | 0,0783 | p5 |
| 6 | Combien de temps avant la fin… | 5 | 1 | 0,0524 | p4 |
| 7 | Mon colis n'est jamais arrivé… | 6 | 1 | 0,1192 | p7 |
| 8 | On m'a facturé un montant… | 7 | 1 | 0,1494 | p3 |
| 9 | …un code envoyé sur mon téléphone ? | 8 | 1 | 0,2180 | p9 |
| 10 | Pendant combien de temps gardez-vous… | 9 | 1 | 0,1062 | p8 |
| 11 | Comment effacer définitivement… | 9 | 1 | 0,0628 | p5 |
| 12 | À quelle heure… en cas de panne ? | 10 | 1 | 0,1959 | p7 |

| Métrique | Résultat | Hasard (référence) |
|---|---|---|
| hit@1 | 12/12 = 100 % | 10 % |
| hit@3 | 12/12 = 100 % | 30 % |
| MRR | 1,00 | 0,29 |

Écart moyen entre la 1re et la 2e page : 0,10 ; écart minimum : 0,0006 (question 2).

**Ce que ça dit**
- La chaîne complète fonctionne : lecture du PDF, découpage, vecteurs `bge-m3`, index, recherche. Elle est très au-dessus du hasard.
- **Ma prédiction était fausse** : le modèle n'a pas hésité sur les paires voisines (7 et 8 : écarts de 0,12 et 0,15).

**Ce que ça ne dit pas**
- Un score parfait ne prouve pas que `bge-m3` est excellent : il prouve que **ce corpus est trop facile pour départager des modèles**. Si Qwen3 ou EmbeddingGemma font aussi 100 %, on ne saura pas lequel est le meilleur.
- Le rang 1 de la question 2 tient à 0,0006 : il est fragile. Le **rang** cache cette fragilité, l'**écart** la révèle.
- 12 questions, un seul corpus fictif, de petites pages bien séparées : ce n'est pas un document réel avec des pages longues, du bruit, des tableaux.

**Suite** : pour la phase 2b (comparer des modèles), il faudra un corpus **plus difficile** (plus de pages, pages plus longues donc plusieurs chunks, sujets plus proches), créé **à côté** de celui-ci, sans modifier celui-ci. On suivra aussi l'écart de score, pas seulement le rang.

## Mesure 2 — réponses avec citations, `llama3.2:3b` (story 03, étape g)

Commande : `mini-rag-eval-answers --runs 1 --show-answers`, lancée sous `caffeinate` (pas de mise en veille).

**Conditions** : recherche `bge-m3`, génération `llama3.2:3b` via Ollama 0.40.16 sur un Mac Intel i7 (100 % processeur, sans carte graphique), température 0, `k = 4`, seuil `0,55`, fenêtre 4096, réponse limitée à 512 tokens. Corpus et 12 questions de la mesure 1, plus 4 questions hors sujet écrites **avant** toute mesure et figées (une très éloignée, trois proches du sujet). **Un seul passage** : la génération n'est pas strictement reproductible, ce résultat est donc un échantillon.

**Prédiction écrite avant la mesure** : « le modèle citera correctement dans moins de la moitié des cas ; les 4 questions hors sujet seront refusées sans appel au modèle. »

**Résultats**

| # | Page attendue | Répondu | Citation vérifiée | Bonne page citée | Durée | Ce que le modèle a fait |
|---|---|---|---|---|---|---|
| 1 | 1 | non | – | – | 83,4 s | « Je ne sais pas » (premier appel : chargement du modèle) |
| 2 | 2 | oui | non | non | 24,4 s | « prélevé le cinq de chaque mois » : juste, sans citation |
| 3 | 2 | non | – | – | 24,8 s | « Je ne sais pas » |
| 4 | 3 | non | – | – | 21,3 s | « Je ne sais pas » |
| 5 | 4 | oui | oui | oui | 36,2 s | pause de 1 à 3 mois, cite [1] |
| 6 | 5 | oui | oui | oui | 21,3 s | préavis de 30 jours, cite [1] |
| 7 | 6 | oui | oui | oui | 38,2 s | remboursement sous 10 jours, cite [1] |
| 8 | 7 | oui | oui | oui | 39,6 s | écrire au service litiges, cite [1] |
| 9 | 8 | oui | non | non | 23,5 s | double vérification : juste, sans citation |
| 10 | 9 | oui | oui | oui | 17,3 s | conservation 3 ans après la fin, cite [1] |
| 11 | 9 | non | – | – | 13,2 s | « Je ne sais pas » |
| 12 | 10 | non | – | – | 15,3 s | « Je ne sais pas » |
| 13 | hors sujet | refus | – | – | 0,5 s | refus par le seuil, sans appel au modèle |
| 14 | hors sujet | refus | – | – | 0,2 s | refus par le seuil, sans appel au modèle |
| 15 | hors sujet | refus | – | – | 11,9 s | **a franchi le seuil** ; le modèle a refusé de lui-même |
| 16 | hors sujet | refus | – | – | 0,3 s | refus par le seuil, sans appel au modèle |

| Métrique | Résultat |
|---|---|
| Réponses données (sur 12 questions du guide) | 7/12 = 58 % |
| Refus à tort (la réponse était dans les documents) | **5/12 = 42 %** |
| Citations vérifiées (parmi les 7 réponses) | 5/7 = 71 % |
| Numéros de citation inventés | 0/7 |
| Bonne page citée (sur 12) | 5/12 = 42 % |
| Refus justifiés (sur 4 hors sujet) | 4/4 = 100 % |
| dont refusés par le seuil seul | 3/4 |
| Réponses inventées hors sujet | 0/4 |
| Tokens / durée totale | 10 083 / 371 s (environ 6,5 minutes) |

**Prédiction contre résultat**
- « Moins de la moitié des cas, citation correcte » : exact en valeur (5/12 = 42 %), mais **pour une autre raison** que celle que je supposais. Le problème principal n'est pas l'oubli de citation (2 réponses sur 7), c'est le **refus à tort** (5 questions sur 12).
- « Les 4 hors sujet refusées sans appel au modèle » : **inexact**. 4 sur 4 sont refusées, mais 3 seulement par le seuil. La question 15 (application mobile) a franchi le seuil et n'a été arrêtée que par le modèle.

**Ce que ça dit**
- **Le critère de la story est atteint** : aucune citation inventée (0/7), aucune réponse inventée hors sujet (0/4). Rien n'est affirmé sans source ou sans que le code le sache.
- **Les 7 réponses données sont conformes au guide** à la lecture, mais seulement 5 sont sourcées.
- Les 5 refus à tort ont tous duré plus de 13 s : le modèle a été appelé, ce n'est donc pas le seuil qui a refusé. D'après la mesure 1, la bonne page était pourtant **en tête** de la recherche pour ces questions. **C'est `llama3.2:3b` qui refuse alors que la réponse figure dans les extraits.**
- Le seuil seul ne suffit pas : sur les 4 hors sujet, 1 l'a franchi. C'est le modèle qui a évité une réponse inventée, ce qui n'est pas garanti.

**Ce que ça ne dit pas**
- **Un seul passage** : on ne connaît pas la variabilité. Un autre passage pourrait changer plusieurs lignes.
- **Toutes les citations valent `[1]`**, c'est-à-dire l'extrait classé premier par la recherche, qui était la bonne page dans 12 cas sur 12. On ne sait donc pas si le modèle **lit** les extraits pour citer, ou s'il écrit `[1]` par habitude. Pour le savoir, il faudrait présenter les extraits dans un ordre où la bonne page n'est pas en tête.
- Les durées sont celles d'un Mac Intel sans carte graphique ; la première question (83 s) inclut le chargement du modèle.
- Le jugement « conforme au guide » est le mien, par lecture : il n'y a pas de réponse de référence automatisée.

**Suite proposée** (un changement à la fois) : (1) répéter ce passage 3 fois pour mesurer la variabilité ; (2) essayer la variante de prompt avec un exemple de réponse citée, que la version TypeScript avait prévue pour les petits modèles, puis comparer sur 3 passages ; (3) ensuite seulement, calibrer le seuil.
