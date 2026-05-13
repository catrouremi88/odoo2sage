# odoo2sage

App web Flask — convertit un export Odoo 17 (.xlsx) en fichier d'import Sage 100 (.txt).

## Déploiement Render

1. Pousser ce repo sur GitHub
2. Créer un Web Service sur Render connecté au repo
3. **Build Command** : `pip install -r requirements.txt`
4. **Start Command** : `gunicorn app:app`

## Mise à jour du référentiel

Pour mettre à jour les codes affaires, remplacer le fichier `CODE_AFFAIRE.xlsx` dans le repo.

## Format de sortie

```
Journal;DatePiece;NumPiece;CompteGeneral;CompteTiers;Libelle;Debit;Credit;DateEcheance;Analytique
```
