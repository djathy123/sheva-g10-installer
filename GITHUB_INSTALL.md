# Installation SHEVA G10 depuis GitHub

Ce dépôt **public** contient uniquement le bootstrap Mac Apple Silicon, les CLI et trois Skills pilotes génériques. Il ne contient pas les dépôts, données, moteurs propriétaires ni secrets SHEVA.

## Installation — une commande, nouveau Mac Apple Silicon

Après avoir examiné [install-remote.sh](install-remote.sh), exécuter dans Terminal :

```bash
curl -fsSL https://raw.githubusercontent.com/djathy123/sheva-g10-installer/v0.3.0/install-remote.sh | bash -s -- --profile full --mission m13 --apply
```

Pour un Mac de 8 Go RAM, remplacer `full` par `controller`. Pour FIGO, remplacer `m13` par `figo`. Pré-requis : macOS ARM64, Command Line Tools Apple, Internet, droits d'installation et >=25 GiB libres pour le profil full.

Le bootstrap récupère **uniquement** l'archive GitHub Release `v0.3.0` et exige son SHA256 épinglé :

```
f5b3c949cb4a6204c5ed299e2a245aca630fc48a3a614f2240ab3551e37cc624
```

Il vérifie aussi les 12 empreintes de fichiers avant de lancer le profil choisi. Il refuse de remplacer silencieusement un autre pack local.

## Prévisualisation sans installer

```bash
curl -fsSL https://raw.githubusercontent.com/djathy123/sheva-g10-installer/v0.3.0/install-remote.sh | bash -s -- --profile full --mission m13
```

## CLI après installation

```bash
~/sheva-g10-installer/sheva-factory roadmap --mission m13
~/sheva-g10-installer/sheva-factory roadmap --mission figo
~/sheva-g10-installer/sheva-factory skills install --mission figo
~/sheva-g10-installer/sheva-factory skills verify --mission figo
~/sheva-g10-installer/sheva-factory worker smoke
~/sheva-g10-installer/sheva-factory supervise --watch --interval 15
```

**Couverture réelle v0.2 :** base d'outils SHEVA + 3 Skills pilotes ; OpenHands / LangGraph / Hatchet nécessitent leur configuration et tests opérationnels ; pgTAP, Langfuse, Backstage et les workers inter-hôtes ne sont pas déployés. Aucun compte Claude/Codex ni secret SHEVA n'est transféré. Les 108 Skills métiers restent à développer. Aucune opération staging/prod ni REAL_RESET autorisée.

**Sécurité :** une commande `curl | bash` exécute du code téléchargé : vérifier la provenance du dépôt et lire le script avant exécution. Pour la reproductibilité, utiliser la version taguée et le SHA256 épinglé, jamais `main` sans validation.


Correction 0.2.1 : CLI symlink resolu et PATH zsh configure automatiquement ; `sheva-factory tools` enumere les **21 composants SHEVA**, Claude et Codex etant suivis separement.
