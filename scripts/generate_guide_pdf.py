"""Fabrique le « Guide client Astrolabe », un corpus d'évaluation ENTIÈREMENT FICTIF de 10 pages.

Usage : python scripts/generate_guide_pdf.py eval/corpus/fictional-customer-guide.pdf

Astrolabe, ses prix, ses délais et ses règles sont inventés pour l'occasion : aucune donnée réelle.
Chaque page traite d'un seul sujet et tient en un chunk. Les pages 2-3, 4-5, 6-7 et 8-9 sont
volontairement voisines (paiement/factures, suspendre/résilier, remboursement/litige,
sécurité/données) pour éprouver la recherche. Une fois les questions écrites, ce texte est figé :
on ne le retouche pas pour améliorer un score.
"""

import sys
import textwrap
from pathlib import Path

from generate_fictional_pdf import write_pdf  # script voisin : Python cherche d'abord dans ce dossier

LINE_WIDTH = 90  # caractères par ligne

DISCLAIMER = "Guide client Astrolabe - document entièrement fictif, créé pour tester une recherche par le sens."

# (titre, texte) : une page par entrée, dans l'ordre.
GUIDE = [
    (
        "1. Créer un compte et choisir une formule",
        "Pour commencer, rendez-vous sur le site d'Astrolabe et cliquez sur Inscription. Il suffit "
        "d'une adresse électronique et d'un mot de passe. Trois formules sont proposées : Essentiel "
        "à 9 euros par mois, Confort à 19 euros par mois avec stockage étendu, et Équipe à 49 euros "
        "par mois pour dix utilisateurs. Un essai gratuit de quatorze jours est offert avec toutes "
        "les formules, sans carte bancaire. Vous recevez ensuite un courriel de bienvenue contenant "
        "un lien de confirmation valable quarante-huit heures. Une fois l'adresse confirmée, le "
        "compte est actif immédiatement.",
    ),
    (
        "2. Dates et moyens de paiement",
        "Le montant de la formule est prélevé le cinq de chaque mois, à l'échéance de la période "
        "commencée. Si le cinq tombe un week-end, le prélèvement a lieu le jour ouvré suivant. Les "
        "moyens de paiement acceptés sont la carte bancaire, le prélèvement SEPA et le portefeuille "
        "électronique PayLoop. Les cartes prépayées ne sont pas acceptées, car elles ne permettent "
        "pas le renouvellement automatique. En cas d'échec du prélèvement, une seconde tentative est "
        "faite quatre jours plus tard.",
    ),
    (
        "3. Factures et justificatifs",
        "Chaque facture est émise le jour du paiement et conservée dans l'espace personnel, rubrique "
        "Documents. Elle est téléchargeable au format PDF pendant dix ans. Un récapitulatif annuel "
        "regroupant tous les montants réglés est disponible chaque mois de janvier. Pour obtenir une "
        "facture au nom de votre entreprise, indiquez sa raison sociale et son numéro de TVA dans la "
        "rubrique Profil avant le prochain paiement. Les factures ne sont jamais envoyées par la "
        "poste.",
    ),
    (
        "4. Changer de formule ou suspendre",
        "Vous pouvez passer à une autre formule à tout moment depuis la rubrique Mon abonnement. Le "
        "changement prend effet immédiatement s'il s'agit d'une formule supérieure, et à la prochaine "
        "échéance s'il s'agit d'une formule inférieure. Il est aussi possible de suspendre le service "
        "pendant une période de un à trois mois, par exemple pendant des vacances. Durant la "
        "suspension, rien n'est facturé et les données restent intactes. Le service reprend "
        "automatiquement à la date choisie.",
    ),
    (
        "5. Résilier le contrat",
        "Le contrat est sans engagement de durée. Pour y mettre fin, utilisez le bouton Résilier "
        "dans la rubrique Mon abonnement, ou écrivez au service client. Un préavis de trente jours "
        "est demandé : la résiliation prend effet à la fin du mois en cours si la demande est faite "
        "au moins trente jours avant. Aucune pénalité n'est appliquée. Après la fin du contrat, "
        "l'accès est coupé, mais vos fichiers restent téléchargeables pendant quatre-vingt-dix jours.",
    ),
    (
        "6. Remboursement d'une commande non reçue",
        "Si une commande de matériel passée auprès d'Astrolabe n'est pas livrée dans les vingt jours "
        "ouvrés, vous pouvez en demander le remboursement intégral. Le suivi du colis est consultable "
        "dans la rubrique Commandes. Après vérification auprès du transporteur, le remboursement est "
        "effectué sous dix jours sur le moyen de paiement utilisé. Aucun justificatif n'est "
        "nécessaire en dehors du numéro de commande. Une commande livrée mais endommagée suit la "
        "même procédure.",
    ),
    (
        "7. Contester un montant débité",
        "Si un montant débité vous semble inexact ou inconnu, ne faites pas opposition auprès de "
        "votre banque tout de suite : écrivez d'abord au service litiges en joignant la facture "
        "concernée et une capture de votre relevé. Un conseiller répond sous cinq jours ouvrés et "
        "peut corriger une erreur de facturation sans frais. Si le désaccord persiste après trente "
        "jours, vous pouvez saisir le médiateur de la consommation, dont les coordonnées figurent en "
        "bas de chaque facture.",
    ),
    (
        "8. Sécurité du compte",
        "Pour mieux protéger votre accès, activez la double vérification dans la rubrique Sécurité. "
        "À chaque connexion depuis un nouvel appareil, un code à six chiffres est envoyé par message "
        "sur votre téléphone ou généré par une application d'authentification. Le code est valable "
        "deux minutes. Nous recommandons aussi un mot de passe d'au moins douze caractères, jamais "
        "réutilisé ailleurs. Après cinq tentatives échouées, le compte est verrouillé pendant quinze "
        "minutes.",
    ),
    (
        "9. Données personnelles",
        "Astrolabe conserve vos informations de compte (nom, adresse électronique, historique de "
        "facturation) pendant toute la durée du contrat, puis trois ans après sa fin pour répondre "
        "aux obligations légales. Passé ce délai, elles sont supprimées automatiquement. Vous pouvez "
        "demander l'effacement anticipé de vos données depuis la rubrique Vie privée ; la demande est "
        "traitée sous trente jours, et seules les factures soumises à une obligation de conservation "
        "sont gardées. Aucune donnée n'est vendue à des tiers.",
    ),
    (
        "10. Assistance",
        "L'assistance technique est joignable du lundi au vendredi de 8 h à 20 h, et le samedi de "
        "9 h à 13 h, heure locale. En cas de panne générale, une page d'état du service est mise à "
        "jour toutes les quinze minutes. Pour les clients de la formule Équipe, une ligne "
        "téléphonique prioritaire est ouverte. Le délai de réponse moyen est de deux heures par "
        "messagerie et de quatre heures par courriel. Aucune intervention n'est possible le "
        "dimanche et les jours fériés.",
    ),
]


def build_pages() -> list[list[str]]:
    """Une page = son titre, une ligne vide, puis le texte découpé en lignes."""
    pages = []
    for number, (title, body) in enumerate(GUIDE):
        lines = [title, ""]
        if number == 0:
            lines = [DISCLAIMER, ""] + lines  # l'avertissement figure en tête de la première page
        # break_on_hyphens=False : « quarante-huit » reste d'un seul tenant en fin de ligne.
        lines += textwrap.wrap(body, LINE_WIDTH, break_on_hyphens=False)
        pages.append(lines)
    return pages


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage : python scripts/generate_guide_pdf.py <file.pdf>", file=sys.stderr)
        return 1
    destination = Path(sys.argv[1])
    destination.write_bytes(write_pdf(build_pages()))
    print(f"{destination} : {len(GUIDE)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
