# SHEVA AI Factory — G10 One-Command Installer v0.2.0

**Objectif:** exécuter une seule commande sur chaque Mac pour installer une base d'outils SHEVA reproductible, puis qualifier les moteurs et l'architecture. Ce bundle **n'est pas encore une release publique** et la distribution automatique depuis Internet n'est pas configurée.

## Exécuter sur le Mac M4 (16 Go / worker ou full)

Simulation sans modification :

```sh
bash ~/sheva-g10-installer/install.sh --profile full
```

Installation réelle (modifie le compte macOS courant : Homebrew, uv tools, packages npm et environnement Python) :

```sh
bash ~/sheva-g10-installer/install.sh --profile full --apply
```

Pour le Mac M1 (8 Go) : `bash ~/sheva-g10-installer/install.sh --profile controller --apply`; cet installateur exige au moins 10 Gio libres et peut refuser l'installation. Pour une machine de calcul : `--profile worker`. Pour un Mac GPU dédié : `--profile gpu`.

Vérification non destructive : `bash ~/sheva-g10-installer/install.sh --profile full --verify`.
Étape isolée (test/maintenance) : `bash ~/sheva-g10-installer/install.sh --profile worker --only python --apply`.

## Couverture — 21 composants SHEVA

- Python / uv tools : graphifyy 0.9.56, specify-cli 1.2.5, semgrep 1.183.0.
- Python venv 3.12 : LangGraph 1.1.10, LangGraph checkpoint SQLite 3.1.3, Hatchet SDK 1.44.0.
- Node local : Agent Canvas 1.34.0, Nx 24.0.3, dependency-cruiser 18.7.0, ast-grep 0.51.0, Orval 8.46.0, ts-rest 3.52.1, MSW 3.0.3, Pact 17.1.4, playwright-core 1.64.1 ; Claude Code CLI 2.1.72 et Codex CLI 0.155.0 (installés sans authentification).
- CLI système : act, Supabase CLI ; Structurizr (profil full) ; Ollama (profil gpu).
- À déployer et tester séparément : OpenHands Agent Server (Canvas fournit un runtime), pgTAP/PostgreSQL isolé, Langfuse, Backstage.
- Applications et comptes non automatisés : Docker Desktop doit être installé et démarré par son propriétaire ; Remote Desktop Commander et l'authentification Claude/Codex exigent une connexion spécifique ; les binaires CLI seuls ne donnent accès à aucun abonnement.
- Les Skills et moteurs SHEVA **propriétaires** doivent être exportés depuis un bundle contrôlé ou un dépôt privé avec droit d'accès. Ils ne sont pas automatiquement clonés sur le Mac d'un tiers. Inventaire constaté sur le M1 : 5 Skills internes dans sheva-ai-factory/skills et 1 Skill local sheva-factory-tools ; le catalogue annoncé de 108 Skills n'est pas entièrement présent/validé.

## Sécurité et intégrité

- Pas de copie de clés, session ChatGPT/Claude, fichier .env, base de production ou dossier personnel.
- Pas de git push, migration, reset, accès à Supabase distant ni création de connexion cloud.
- Les paquets sont explicitement versionnés pour Python et Node. Les versions de Homebrew restent soumises au dépôt de formules (le bundle n'est **pas** un lockfile de dépendances système ni une supply chain vérifiée par digest).
- Un agent Canvas lancé directement sur l'hôte peut accéder aux ressources du compte utilisateur : choisir Docker/VM sandbox avant travail sur un dépôt sensible.
- L'installateur ne démarre pas les serveurs, ne certifie pas les health checks ni les 21 outils actifs. Rapports sous ~/sheva-toolchain/reports/last-install.json après --apply/--verify.
- Réexécutable : réutilise les formules Brew et environnements gérés ; les phases npm/uv réappliquent les versions épinglées. Les commandes externes peuvent nécessiter réseau, espace disque et autorisations macOS.
- Rollback : ne supprimer qu'après inspection du répertoire géré ~/sheva-toolchain. Les installations Homebrew/uv sont globales au compte et ne sont pas automatiquement annulées. Ne jamais supprimer de conteneurs/volumes sans audit.

## État du développement

- Version v0.2.0 : vérification de la syntaxe, plan et inventaire non destructifs sur Mac M1 et M4.
- Non testé au moment de la publication : installation intégrale sur machine vierge, échec et reprise par étape, connexion durable OpenHands / Hatchet / LangGraph, worker distribué, restauration de données réelles, Linux x86_64.
- Le prochain jalon est un test réel en laboratoire M4 avec consentement du propriétaire, puis un paquet versionné distribuable par une URL vérifiée. Ne pas inventer une URL d'installation avant publication.


## CLI autonome G10 — sans dépendance à ChatGPT
Une fois le ZIP extrait vers `~/sheva-g10-installer/`, utiliser directement le CLI local :
```bash
~/sheva-g10-installer/sheva-factory roadmap --mission m13
~/sheva-g10-installer/sheva-factory roadmap --mission figo
~/sheva-g10-installer/sheva-factory status --mission m13
~/sheva-g10-installer/sheva-factory install --profile full --mission m13 --apply
~/sheva-g10-installer/sheva-factory skills list --mission m13
~/sheva-g10-installer/sheva-factory skills install --mission figo
~/sheva-g10-installer/sheva-factory skills verify --mission figo
~/sheva-g10-installer/sheva-factory skills rollback --mission figo
~/sheva-g10-installer/sheva-factory worker status
~/sheva-g10-installer/sheva-factory worker smoke
~/sheva-g10-installer/sheva-factory supervise once
~/sheva-g10-installer/sheva-factory supervise --watch --interval 15
~/sheva-g10-installer/sheva-factory reports
```
Le raccourci `~/.local/bin/sheva-factory` est installé localement sur les machines testées. Un Mac neuf ne requiert pas ce raccourci : le chemin `~/sheva-g10-installer/sheva-factory` fonctionne directement après extraction.

Les données d'état sont recomputées à chaque exécution, sans mémoire du chat : présence des composants, santé des services Docker/Canvas/Agent Server, empreintes et présence des Skills installés, derniers rapports, roadmap et blocages. Une copie machine-locale est conservée sous `~/sheva-toolchain/reports/roadmap.json` et `supervision.json`; `worker-smoke.json` contient une preuve de test synthétique. Pour le mode `--watch`, laisser le Terminal ouvert ; ce n'est pas un daemon persistant.

`install --apply` écrit au fur et à mesure `~/sheva-toolchain/reports/last-apply.json` et `install-history.jsonl` après chaque étape. Lancer à nouveau la commande pour retenter les étapes échouées (le succès complet d'une réinstallation idempotente après panne reste à qualifier). `--verify` génère `last-verify.json` sans effacer le dernier rapport d'installation.

**Scope G10 v0.2 :** 23 composants surveillés (21 de la matrice initiale + Claude/Codex CLI), trois Skills pilotes versionnés ; le but de 108 Skills est encore un backlog. Le CLI ne donne aucun compte IA à une autre personne, ne télécharge pas de moteur SHEVA privé, ne relie pas les workers entre ordinateurs et n'autorise aucun reset/staging/production. L'état `INSTALLED` prouve la présence d'un composant, pas que son agent est authentifié.


## Distribution autonome Mac Apple Silicon — v0.2.0

Télécharger le ZIP `SHEVA_AI_FACTORY_G10_MAC_ARM64_v0.2.zip` puis le placer dans `~/Downloads/`.

**Une seule commande pour une machine neuve** (décompresse et installe le profil complet et les Skills M13) :

```bash
bash -c 'set -e; z="$HOME/Downloads/SHEVA_AI_FACTORY_G10_MAC_ARM64_v0.2.zip"; d="$HOME/sheva-g10-installer"; test -f "$z" || { echo "Archive absente: $z"; exit 1; }; mkdir -p "$d"; /usr/bin/unzip -oq "$z" -d "$d"; /bin/bash "$d/bootstrap-macos.sh" --profile full --mission m13 --apply'
```

Simulation préalable sans téléchargement de packages :

```bash
bash -c 'set -e; z="$HOME/Downloads/SHEVA_AI_FACTORY_G10_MAC_ARM64_v0.2.zip"; d="$HOME/sheva-g10-installer"; mkdir -p "$d"; /usr/bin/unzip -oq "$z" -d "$d"; /bin/bash "$d/bootstrap-macos.sh" --profile full --mission m13'
```

Pour un Mac à 8 Go, remplacer `--profile full` par `--profile controller`; pour FIGO, choisir `--mission figo` (Skills pilotes FIGO chargés à la demande). Après installation : `~/sheva-g10-installer/sheva-factory roadmap --mission m13`.

**Prérequis réels :** macOS Apple Silicon (ARM64, macOS 14+), accès Internet, Command Line Tools Apple, Homebrew (le bootstrap propose de l'installer si absent), droits de modification du Mac et environ 25 Gio libres pour `full`. L'installation Docker Desktop peut demander des autorisations macOS. Les outils de CLI Claude/Codex s'installent sans connecter les comptes personnels.

**Sécurité :** vérifier la source et l'empreinte SHA256 de l'archive avant exécution ; le script vérifie les empreintes SHA256 internes de chaque fichier. Le pack ne contient ni mots de passe ni identifiants ni code client. Sur le Mac d'un tiers, ne pas connecter tes comptes privés sans environnement sécurisé.

**Couverture :** 21 composants de l'architecture plus Claude/Codex CLI surveillés, dont des services qui ne sont pas activés automatiquement (Langfuse, Backstage, pgTAP); seulement trois Skills pilotes fournis ; les 108 Skills prévus restent à créer/évaluer. OpenHands peut démarrer séparément et l'authentification des agents est volontairement séparée de l'installation. Le statut d'installation PASS n'est pas une certification de mission ou de production.

**Distribution :** cette archive n'a pas d'URL publique GitHub vérifiée. Ne pas employer `curl https://... | bash` avec une URL inventée. Pour installation sur une autre machine, utiliser le ZIP vérifié téléchargé ici ou une future release officiellement publiée.
