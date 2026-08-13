# Fonds visio

10 fonds d'écran pour l'Incrustation du présentateur (macOS) et les appels visio.
Dégradés doux en tons sombres, pour que le visage ressorte sans que le fond attire l'œil.

Format : PNG 1920 × 1080.

## Les utiliser

1. Lancer le partage d'écran (FaceTime, Zoom, Teams…) et activer l'incrustation
2. Centre de contrôle (en haut à droite) → **Effets vidéo** → **Arrière-plan**
3. Bouton **+** en bas de la liste → choisir un fichier de ce dossier

Une fois ajoutés, ils restent dans la liste d'un enregistrement à l'autre.

## Les regénérer

```sh
swift generer-fonds.swift
```

Écrit les PNG dans `~/Pictures/Fonds visio`. Aucune dépendance à installer :
le script s'appuie sur CoreGraphics et CoreImage, fournis avec macOS.

Pour changer les couleurs, modifier le tableau `palettes` en haut du script.
Chaque entrée = une couleur de fond plus quelques taches de couleur, le tout
passé au flou. Les positions sont en fraction de l'image (0 à 1), le rayon en
fraction de la largeur.
