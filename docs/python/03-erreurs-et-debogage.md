# Lire une erreur Python et déboguer

## Lire une « trace » (traceback)
```
Traceback (most recent call last):
  File "src/mini_rag/chunking.py", line 12, in split
    return texte[debut:fin]
TypeError: 'NoneType' object is not subscriptable
```
1. **Lire de bas en haut** : la dernière ligne dit *quoi* (`TypeError`, le message). Les lignes au-dessus disent *où* : la plus basse est la ligne fautive, les précédentes sont la chaîne d'appels.
2. Ici : `texte` valait `None`. La vraie question n'est pas « ligne 12 » mais « qui a donné `None` à `split` ? ».
3. Former une **hypothèse écrite** avant de demander de l'aide, puis la vérifier.

## Erreurs fréquentes
| Erreur | Signification probable |
|---|---|
| `ModuleNotFoundError` | paquet non installé, ou environnement virtuel non activé |
| `IndentationError` | indentation incohérente (mélange tabulations/espaces) |
| `KeyError: 'x'` | clé absente d'un dict : utiliser `.get` ou vérifier les données |
| `AttributeError: 'NoneType' ...` | une valeur est `None` là où on attendait un objet |
| `TypeError` | mauvais type d'argument ou mauvais nombre d'arguments |
| `ValueError` | bon type, mauvaise valeur (ex. `int("abc")`) |
| `ImportError` / import circulaire | deux modules s'importent mutuellement |
| `RuntimeWarning: coroutine ... was never awaited` | fonction `async` appelée sans `await` |

## Outils
- `pytest -x` : s'arrête au premier échec ; `pytest -k motif` : lance les tests dont le nom contient `motif` ; `pytest -vv` : détails.
- `breakpoint()` : ouvre le débogueur interactif (`n` ligne suivante, `c` continuer, `p variable` afficher, `q` quitter).
- `print(repr(x))` : voir la vraie valeur, y compris les espaces et sauts de ligne cachés.
- Réduire le problème : isoler la plus petite entrée qui reproduit l'erreur, et en faire un **test** avant de corriger (TDD).

## Règle du projet : un bug corrigé à la main
Pour chaque projet, au moins un bug réel est corrigé **par toi**, avec l'hypothèse écrite **avant** de demander de l'aide. Les consigner dans `docs/journal.md` (symptôme, hypothèse, cause trouvée, correction, ce que ça t'apprend).
