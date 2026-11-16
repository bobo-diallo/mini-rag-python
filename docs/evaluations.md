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
