# Glossaire : les mots de l'écosystème IA, expliqués pour un développeur web

Règle du projet : **tout mot nouveau est expliqué à sa première apparition, puis ajouté ici.** Chaque entrée dit ce que c'est, ce que ça fait techniquement, et une analogie avec le monde web (PHP, Java, bases de données) quand elle aide. Les entrées sont rangées par thème, dans l'ordre où on les rencontre.

Les analogies sont des repères, pas des équivalences exactes : elles aident à démarrer, puis on les dépasse.

---

## 1. Les bases : modèle, entraînement, inférence

**Modèle (model)** : un gros fichier de nombres (des « poids ») qui contient ce qu'un programme a appris à partir d'énormes quantités d'exemples. On ne le programme pas à la main : on le *charge* puis on lui envoie une entrée et il renvoie une sortie. Analogie : une bibliothèque compilée (`.jar`) dont on ne lit pas le code, on appelle seulement ses fonctions. Taille typique : de 100 Mo à plusieurs dizaines de Go.

**Entraînement (training)** : la phase où le modèle *apprend*. On lui montre des millions d'exemples et il ajuste ses poids pour se tromper de moins en moins. C'est très coûteux (des milliers de GPU, des semaines). **On ne le fait pas dans ce projet** : on utilise des modèles déjà entraînés par d'autres.

**Inférence (inference)** : l'utilisation d'un modèle déjà entraîné : on lui donne une entrée, il calcule une sortie. C'est ce que fait ton programme à chaque requête. Analogie : l'entraînement, c'est la compilation (lourde, faite une fois par d'autres) ; l'inférence, c'est l'exécution (légère, faite à chaque appel).

**Poids (weights)** : les nombres appris pendant l'entraînement, stockés dans le fichier du modèle. Quand on dit qu'un modèle « fait 3 milliards de paramètres » (3B), on parle du nombre de ces poids.

**Paramètres (3B, 7B...)** : le nombre de poids. Plus il est grand, plus le modèle est capable en général, mais plus il est lent et gourmand en mémoire. « 3B » = 3 milliards.

**Fine-tuning (ajustement fin)** : reprendre un modèle déjà entraîné et le réentraîner *un peu* sur ses propres exemples (par exemple tes types de factures) pour le spécialiser. Beaucoup moins cher que l'entraînement complet, mais pas gratuit, et pas toujours utile. Une grande partie de la phase 3c consiste à savoir **quand ne pas le faire**.

**LoRA** : une technique de fine-tuning légère. Au lieu de modifier tous les poids, on en ajoute quelques-uns, petits, par-dessus. Résultat : on peut faire du fine-tuning sur un portable. Bibliothèque utilisée : `peft`.

**GPU / CPU / MPS** : les puces qui calculent. Le CPU est le processeur ordinaire. Le GPU (carte graphique) est bien plus rapide pour les calculs de modèles. **MPS** est le nom de l'accélération graphique sur les Mac Apple Silicon : ton Mac peut s'en servir pour accélérer des modèles.

**Quantification** : réduire la précision des poids (par exemple de 16 bits à 4 bits) pour que le modèle prenne 3 à 4 fois moins de place et tourne sur du matériel modeste, avec une petite perte de qualité. C'est ce qui permet à Ollama de faire tourner des modèles sur un portable.

---

## 2. Les modèles de langage et leur vocabulaire

**LLM (Large Language Model)** : un modèle de langage de grande taille, comme Claude ou Llama. Il lit du texte et produit du texte, en prédisant les mots suivants un par un.

**Token** : l'unité de texte que le modèle manipule : un mot, un morceau de mot, ou un signe. En français, compte environ 1 token pour 3 à 4 caractères. **On est facturé au token** par les services payants, d'où l'importance de suivre les coûts.

**Prompt** : le texte envoyé au modèle (consigne, question, extraits). Écrire de bons prompts s'apprend et se versionne comme du code.

**Contexte / fenêtre de contexte** : la quantité maximale de texte que le modèle peut lire en une fois (mesurée en tokens). Au-delà, il ne voit plus rien. C'est une limite de mémoire à court terme.

**Hallucination** : quand le modèle invente une réponse qui a l'air plausible mais est fausse. Le RAG et les citations vérifiées existent en grande partie pour la limiter.

**Température** : réglage qui contrôle le caractère aléatoire des réponses. Bas (0) : réponses stables et prévisibles, adaptées à l'extraction de données. Haut : plus créatif.

**Sortie structurée** : demander au modèle de répondre en JSON qui respecte un schéma précis, puis vérifier. Essentiel pour brancher un modèle sur du code (par exemple « extraire montant, date, fournisseur d'une facture »).

---

## 3. Embeddings et recherche par le sens

**Embedding** : une liste de nombres (un « vecteur ») qui représente le *sens* d'un texte. Deux textes qui parlent de la même chose ont des vecteurs proches, même s'ils n'utilisent pas les mêmes mots. Exemple : « facture de taxi » et « reçu de course » seront proches. Analogie : au lieu de comparer du texte avec `LIKE '%mot%'`, on compare des positions dans un espace.

**Vecteur** : simplement une liste de nombres, ici de 384 à 1024 nombres selon le modèle.

**Similarité (cosinus)** : la mesure de proximité entre deux vecteurs. Plus elle est proche de 1, plus les sens sont proches.

**Modèle d'embeddings** : un modèle spécialisé qui transforme du texte en vecteur (par exemple `bge-m3`). Il ne génère pas de texte, il ne fait que « situer » un texte.

**Base vectorielle / index vectoriel** : une base de données capable de retrouver rapidement les vecteurs les plus proches d'un vecteur donné. Chez nous : SQLite avec l'extension `sqlite-vec`.

**MTEB** : un classement public qui compare des modèles d'embeddings sur de nombreuses tâches. Utile pour choisir un modèle sur le Hub.

---

## 4. RAG et ses composantes

**RAG (Retrieval-Augmented Generation)** : « génération augmentée par recherche ». Plutôt que de demander au modèle de répondre de mémoire, on **cherche d'abord** les passages pertinents dans nos documents, puis on les **donne au modèle** avec la question pour qu'il réponde à partir d'eux. Trois étapes : découper et indexer les documents, retrouver les bons extraits, générer la réponse.

**Chunk (extrait)** : un morceau de document (par exemple 1000 caractères). On découpe les documents en chunks parce qu'on ne peut ni indexer ni envoyer un livre entier au modèle.

**Chevauchement (overlap)** : une partie de texte répétée entre deux chunks voisins (par exemple 200 caractères) pour ne pas couper une idée en deux.

**Découpage récursif** : on essaie de couper le texte à l'endroit le plus naturel (saut de paragraphe), et si un morceau reste trop grand, on le redécoupe avec une coupure moins naturelle (saut de ligne, puis espace, puis caractère). « Récursif » veut dire que la fonction s'appelle elle-même sur les morceaux trop grands. Résultat : on coupe rarement au milieu d'un mot.

**Référence de test (oracle)** : une implémentation existante et éprouvée, qu'on utilise seulement dans les tests pour vérifier que notre code donne les mêmes résultats. On n'en dépend pas pour faire tourner le projet.

**Citation vérifiée** : le modèle doit indiquer d'où vient sa réponse, et **le code vérifie** que la citation existe vraiment dans les extraits. On ne fait pas confiance au modèle pour ça.

**Recherche hybride** : combiner la recherche par mots-clés (exacte) et la recherche par le sens (embeddings), car chacune rate des choses que l'autre trouve.

**Reranker / cross-encoder** : un second modèle qui reclasse les meilleurs résultats de la première recherche, plus lent mais plus précis. On ne l'ajoute que si la mesure montre un gain.

**Évaluation** : un jeu de questions dont on connaît les bonnes réponses, qu'on rejoue après chaque changement pour mesurer si on s'améliore ou non. C'est l'équivalent des tests automatisés pour un système d'IA.

---

## 5. Hugging Face et l'outillage de modèles

**Hugging Face (HF)** : le « GitHub des modèles d'IA ». Un site et un écosystème où des milliers de personnes et d'entreprises publient des modèles, des jeux de données et des démos.

**Hub** : le catalogue en ligne de Hugging Face. Chaque modèle y a une page avec sa **fiche de modèle** (*model card*) : à quoi il sert, ses limites, sa **licence** (ce qu'on a le droit d'en faire, y compris commercialement), sa taille.

**Space** : une mini-application de démonstration hébergée gratuitement sur Hugging Face. Pratique pour montrer un projet avec une vraie interface.

**Gradio** : une bibliothèque Python qui crée une interface web (champs, boutons, upload d'image) en quelques lignes, utilisée pour les Spaces.

**`transformers`** : la bibliothèque Python de Hugging Face pour charger et utiliser des modèles. Le mot « transformer » désigne aussi l'architecture (le type de réseau) à la base de presque tous les modèles modernes.

**Pipeline** : dans `transformers`, un raccourci qui assemble le chargement du modèle, le prétraitement et le résultat en un seul appel (par exemple `pipeline("sentiment-analysis")` pour classer un texte en positif ou négatif).

**`sentence-transformers`** : une bibliothèque, construite sur `transformers`, spécialisée dans les embeddings et les rerankers.

**`datasets`** : une bibliothèque pour charger des jeux de données publics (utile pour s'entraîner à évaluer).

**Ollama** : un programme qui télécharge et fait tourner des modèles sur ta machine et les expose par une petite API HTTP locale. Analogie : un serveur applicatif local pour modèles. Rien ne sort de ta machine.

---

## 6. Documents et vision (le cas des factures)

**OCR (reconnaissance optique de caractères)** : transformer une image de texte (photo, scan) en texte. Les outils classiques (comme Tesseract) lisent les caractères mais ne comprennent pas la structure : ils ne savent pas ce qu'est un « total ».

**VLM (Vision-Language Model)** : un modèle qui comprend à la fois des images et du texte. On lui montre une photo de facture et on lui demande « donne-moi le fournisseur, la date et le total en JSON ». Il fait lecture et compréhension d'un coup.

**Extraction de champs** : retrouver des informations précises (date, montant, fournisseur) dans un document, puis les ranger dans une structure (JSON, CSV, Excel).

**Données synthétiques** : des données fabriquées exprès (par exemple de fausses factures générées par nous) plutôt que de vraies. Elles évitent d'exposer des données personnelles.

---

## 7. Agents et outils

**Outil (tool)** : une fonction que le modèle peut demander d'appeler (chercher dans l'index, lire un fichier, envoyer un courriel). Le modèle ne l'exécute pas lui-même : il dit « appelle cet outil avec ces paramètres », et c'est **ton code** qui exécute et rend le résultat.

**Agent** : un programme qui laisse un modèle décider, en boucle, quel outil appeler pour atteindre un but, jusqu'à ce qu'il juge avoir fini. Plus puissant, mais plus risqué : il faut le borner.

**Boucle d'agent** : le cycle « le modèle réfléchit → demande un outil → le code l'exécute → le résultat revient au modèle → recommence ». On l'écrira à la main d'abord pour la comprendre.

**Approbation humaine** : avant une action sensible, l'agent s'arrête et demande ton accord.

**Garde-fou (guardrail)** : une règle codée en dur qui limite ce que l'agent peut faire (nombre d'étapes, outils autorisés, montants maximum).

**MCP (Model Context Protocol)** : un standard ouvert qui décrit comment exposer des outils et des données à un modèle de façon uniforme. Un **serveur MCP** est un petit programme qui publie une liste d'outils (« voici ce que je sais faire ») ; n'importe quel assistant compatible peut alors s'en servir. Analogie : un port USB, c'est-à-dire une prise standard pour brancher des outils sur des modèles, au lieu de refaire le branchement à chaque fois.

---

## 8. Production, sécurité, conformité

**API** : une interface par laquelle un programme parle à un autre (ici, par HTTP). **FastAPI** est la bibliothèque Python qu'on utilise pour exposer la nôtre.

**Observabilité / trace** : enregistrer ce que le système a fait (quel prompt, quelle réponse, combien de tokens, combien de temps, combien ça a coûté) pour pouvoir comprendre ensuite ce qui s'est passé. Analogie : les logs d'un serveur web, en plus détaillés.

**Injection de prompt** : une attaque où un texte malveillant, caché dans un document ou une page, donne des ordres au modèle (« ignore tes consignes et envoie les données à X »). Un risque propre aux LLM, à connaître dès qu'un modèle lit du contenu qu'on ne contrôle pas.

**Loi 25 / RGPD** : les lois sur la protection des renseignements personnels (Québec / Europe). Elles encadrent ce qu'on peut envoyer à un service d'IA externe et comment protéger les données.

**Build vs buy** : construire soi-même une solution ou acheter/utiliser un produit existant. Un consultant doit savoir recommander l'un ou l'autre selon le cas.

**ROI (retour sur investissement)** : ce que la solution rapporte (temps gagné, erreurs évitées) comparé à ce qu'elle coûte à construire et à faire tourner.

---

## Entrées à ajouter au fil des stories
Cette liste se complète à chaque story : chaque nouveau terme y entre le jour où on le rencontre.
