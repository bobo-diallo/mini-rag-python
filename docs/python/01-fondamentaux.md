# Fondamentaux de Python (pour qui connaît PHP et JavaScript)

Objectif : **lire** n'importe quel code Python et comprendre ce qu'il fait. Ce n'est pas un cours complet : on garde ce qui change vraiment par rapport à PHP/JS. Les exemples sont courts ; chaque section dit à quoi s'attendre quand on lit du code généré.

## 1. Ce qui surprend en premier
| Sujet | PHP / JS | Python |
|---|---|---|
| Blocs | `{ ... }` | **indentation** (4 espaces) après un `:` |
| Fin d'instruction | `;` | rien |
| Commentaire | `//` | `#` |
| Docstring | PHPDoc | une chaîne `"""..."""` en première ligne de la fonction/classe |
| Variables | `$x` / `let x` | `x = 1` (pas de mot-clé de déclaration) |
| Vrai/faux/rien | `true false null` | `True False None` (majuscule) |
| Et/ou/non | `&& \|\| !` | `and or not` |
| Égalité | `=== ` | `==` (valeur) ; `is` (même objet, surtout pour `None`) |
| Condition | `else if` | `elif` |
| Ternaire | `a ? b : c` | `b if a else c` |
| Chaîne avec variables | `"$x"` / `` `${x}` `` | `f"{x}"` (f-string) |
| Tableau | `[]` / `Array` | `list` ; l'objet clé-valeur est un `dict` |
| `this` | `$this` / `this` | **`self`, déclaré explicitement** en 1er paramètre des méthodes |

Python est **dynamique** (le type est sur la valeur, pas sur la variable) mais **fortement typé** : `"1" + 1` lève une erreur, il n'y a pas de conversion silencieuse comme en JS.

## 2. Les types de base
```python
nom = "Bobo"          # str
age = 30              # int (taille illimitée)
prix = 9.99           # float
actif = True          # bool
rien = None           # absence de valeur
```
- **Faux** (« falsy ») : `False`, `None`, `0`, `""`, `[]`, `{}`, `set()`. Tout le reste est vrai. On écrit `if not liste:` pour « liste vide ».
- Division : `/` donne toujours un `float` ; `//` donne la division entière ; `**` est la puissance.

## 3. Les collections (à connaître par cœur, elles sont partout)
```python
notes = [12, 15, 9]              # list : ordonnée, modifiable        (≈ array JS)
point = (3, 4)                   # tuple : ordonné, NON modifiable
uniques = {1, 2, 3}              # set : sans doublon, sans ordre
fiche = {"nom": "Bobo", "age": 30}   # dict : clé → valeur            (≈ objet JS / tableau associatif PHP)
```
Opérations courantes :
```python
notes.append(7)                  # ajoute
len(notes)                       # taille
notes[0]; notes[-1]              # premier ; dernier
notes[1:3]                       # tranche (slice) : index 1 inclus, 3 exclu
fiche["nom"]                     # lève KeyError si la clé manque
fiche.get("ville", "inconnue")   # valeur par défaut si manquante
for cle, valeur in fiche.items():
    print(cle, valeur)
```
**Compréhensions** (très présentes dans le code généré) : une boucle écrite en une ligne.
```python
carres = [n * n for n in notes if n > 10]          # list comprehension
longueurs = {mot: len(mot) for mot in ["a", "bcd"]}  # dict comprehension
```
Lecture : « pour chaque `n` de `notes`, si `n > 10`, garder `n * n` ».

Fonctions utiles : `enumerate(liste)` (index + valeur), `zip(a, b)` (parcourir deux listes ensemble), `sorted(liste, key=...)`, `sum`, `min`, `max`, `any`, `all`.

## 4. Fonctions
```python
def saluer(nom: str, politesse: str = "Bonjour") -> str:
    """Rend une salutation."""
    return f"{politesse} {nom}"

saluer("Bobo")                       # positionnel
saluer("Bobo", politesse="Salut")    # par nom (keyword)
```
- `*args` regroupe les arguments positionnels en tuple ; `**kwargs` regroupe les arguments nommés en dict. Se lit « tout ce qui reste ».
- `lambda x: x * 2` : petite fonction anonyme (une seule expression).
- **Piège classique** : ne jamais mettre une liste ou un dict comme valeur par défaut (`def f(x=[])`) : la même liste est partagée entre tous les appels. On met `None` et on crée la liste dans la fonction.
- Une fonction sans `return` rend `None`.

## 5. Types annotés (« type hints »)
Les annotations `nom: str`, `-> str`, `list[str]`, `dict[str, int]`, `str | None` **ne sont pas vérifiées à l'exécution** : elles documentent, aident l'éditeur, et servent à des outils (mypy) et à des bibliothèques (pydantic, FastAPI) qui, eux, les exploitent. Équivalent de TypeScript, mais facultatif et non appliqué par Python lui-même.

## 6. Classes et dataclasses
```python
class Chunk:
    def __init__(self, text: str, page: int):   # constructeur
        self.text = text
        self.page = page

    def preview(self) -> str:
        return self.text[:40]
```
Très souvent on utilise une **dataclass**, qui génère le constructeur et l'égalité :
```python
from dataclasses import dataclass

@dataclass(frozen=True)        # frozen : non modifiable, comme un « value object » du DDD
class Chunk:
    text: str
    page: int
```
- `@truc` au-dessus d'une fonction ou classe est un **décorateur** : il enveloppe ce qu'il décore. À lire comme « on applique `truc` à ce qui suit ».
- Méthodes « magiques » `__init__`, `__repr__`, `__eq__`… : entourées de doubles tirets bas, appelées par Python lui-même.
- Un `_nom` avec un tiret bas devant signale « usage interne » (convention, pas une interdiction).
- Les interfaces : `Protocol` (typage structurel, proche des interfaces TypeScript) ou classe abstraite (`abc.ABC`).

## 7. Erreurs
```python
try:
    valeur = int(texte)
except ValueError as erreur:
    print(f"Pas un nombre : {erreur}")
else:
    ...          # exécuté si aucune erreur
finally:
    ...          # toujours exécuté

raise ValueError("message")   # lever une erreur (≈ throw)
```
On attrape l'erreur **précise**, pas `except Exception:` à tout va (cela masque les bugs).

## 8. Contexte « with » et fichiers
```python
from pathlib import Path

texte = Path("data/note.txt").read_text(encoding="utf-8")

with open("sortie.txt", "w", encoding="utf-8") as fichier:   # ferme le fichier tout seul, même en cas d'erreur
    fichier.write("bonjour")
```
`with` gère l'ouverture et la fermeture (fichier, connexion de base de données, verrou). Préférer `pathlib.Path` aux chaînes pour les chemins.

## 9. Modules, paquets, imports
- Un fichier `.py` est un **module**. Un dossier avec `__init__.py` est un **paquet**.
- `import json` ; `from pathlib import Path` ; `from mini_rag.chunking import split`.
- `if __name__ == "__main__":` : le bloc ne s'exécute que si le fichier est lancé directement, pas quand il est importé.
- Imports circulaires : deux modules qui s'importent l'un l'autre cassent au démarrage ; on les évite en séparant les responsabilités (même discipline que le DDD).

## 10. Environnement et dépendances
- Un **environnement virtuel** (`.venv`) isole les bibliothèques d'un projet. Toujours l'activer : `source .venv/bin/activate`.
- `pip install xxx` installe dans l'environnement actif. Les dépendances du projet sont déclarées dans `pyproject.toml` (équivalent de `package.json`).
- Sans environnement activé, on installe sans le vouloir dans le Python du système : c'est la première source de « ça marche chez moi ».

## 11. Asynchrone
```python
import asyncio

async def interroger() -> str:
    await asyncio.sleep(1)      # « attends sans bloquer les autres »
    return "ok"

resultat = asyncio.run(interroger())
```
- Même idée que `async/await` en JS. Une fonction `async def` ne s'exécute que si on l'`await` ou qu'on la lance via `asyncio.run`.
- **Piège** : appeler une fonction bloquante (lecture réseau synchrone, `time.sleep`) dans du code asynchrone gèle tout le serveur.
- FastAPI accepte les deux (`def` et `async def`). Règle simple pour débuter : `async def` seulement si on utilise un client asynchrone ; sinon `def`.

## 12. Générateurs
```python
def lire_pages(chemin):
    for page in extraire(chemin):
        yield page            # produit une valeur à la fois, sans tout charger en mémoire
```
`yield` fait de la fonction un **générateur** : on le parcourt avec `for`. Utile pour de gros documents.

## 13. Pièges de lecture à retenir
- `==` compare les valeurs, `is` l'identité : `x is None` (jamais `x == None`).
- Les listes et dicts sont **passés par référence** : modifier l'argument dans la fonction modifie l'original. `copy()` pour dupliquer.
- Une indentation décalée change le sens du programme (il n'y a pas d'accolades pour le montrer).
- `for` sur un dict donne les **clés**.
- Les nombres flottants : `0.1 + 0.2 != 0.3` (comme en JS).
- `print` ne sert qu'à déboguer ; pour du vrai suivi on utilise le module `logging`.

## Autotest (si tu sais répondre sans regarder, la section est acquise)
1. Que vaut `[n for n in range(5) if n % 2 == 0]` ?  → `[0, 2, 4]`
2. Pourquoi `def f(x=[])` est-il dangereux ?  → la liste par défaut est créée une seule fois et partagée.
3. Que fait `@dataclass(frozen=True)` ?  → génère constructeur et égalité ; l'objet devient non modifiable.
4. Que renvoie `d.get("x")` si la clé manque ?  → `None`, sans erreur.
5. Quelle différence entre `def` et `async def` ?  → la seconde est une coroutine, à `await`-er ou lancer via `asyncio.run`.
