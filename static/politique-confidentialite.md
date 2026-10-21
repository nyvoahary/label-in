# Politique de confidentialité et d'utilisation des données

**Version : DOC_VERSION v0.1 (brouillon, 21 octobre 2026)**
Plateforme Label-in, corpus de parole malgache PROVA-MG.

> **Brouillon.** Les passages marqués **[À COMPLÉTER]** attendent une décision du responsable du projet. Ce texte doit être relu par l'université ou le délégué à la protection des données avant d'être considéré comme définitif.

---

## Sommaire

1. Qui est responsable
2. À quoi sert la plateforme
3. Les enregistrements audio
4. Les données des comptes
5. Cookies et stockage dans le navigateur
6. Hébergement et transferts
7. Durées de conservation
8. Engagement de confidentialité des transcripteurs
9. Publication du corpus
10. Vos droits
11. Modifications

---

## 1. Qui est responsable

| | |
|---|---|
| Responsable du traitement | **[À COMPLÉTER : nom, qualité (doctorant, laboratoire…)]** |
| Établissement | **[À COMPLÉTER : université, école doctorale, directeur de thèse]** |
| Contact | **[À COMPLÉTER : adresse e-mail dédiée]** |
| Cadre juridique | Loi n° 2014-038 du 9 janvier 2015 sur la protection des données à caractère personnel (Madagascar). **[À COMPLÉTER : préciser si le RGPD s'applique, par exemple partenaire ou financement européen.]** |

---

## 2. À quoi sert la plateforme

Label-in sert à **transcrire et vérifier des segments audio en malgache** (avec passages en français) pour constituer le corpus PROVA-MG. Le corpus sert à :

- entraîner et évaluer des modèles de reconnaissance automatique de la parole pour le malgache ;
- la recherche **[À COMPLÉTER : intitulé de la thèse ou du projet]**.

Les données ne sont ni vendues, ni utilisées pour de la publicité, ni pour du profilage des personnes.

---

## 3. Les enregistrements audio

### 3.1 Origine

**[À COMPLÉTER : pour chaque source (Aotra_zo, aotra_njaka, Fiderana_Rajaonarivelo, storytown_bolo, tea_time_tokatrano…), indiquer d'où vient l'audio (émission, podcast, enregistrement réalisé pour le projet), qui en détient les droits et sur quelle base il est utilisé (autorisation, consentement des locuteurs, exception de recherche).]**

### 3.2 Ce que contiennent les segments

Les enregistrements contiennent des voix. Une voix, et parfois ce qui est dit, peut permettre d'identifier une personne. Le traitement suit donc les règles de la convention de transcription :

- les informations qui identifient une **personne privée** (téléphone, adresse, nom complet d'un particulier, numéro de compte…) sont remplacées par la balise `[personnel]` dans la transcription et le segment est signalé *données personnelles* ([règle 6.1](/documentation#regle-6-1)) ;
- un segment sur un sujet sensible concernant une personne privée identifiable (santé, conflit familial, mineur) est **exclu** avec la raison *contenu sensible* ;
- les segments signalés *données personnelles* sont exclus de l'entraînement et de toute publication tant que l'audio n'est pas masqué (bip ou silence sur la zone).

### 3.3 Qui y a accès

- Les **administrateurs** du projet voient tous les segments et peuvent les télécharger.
- Un **transcripteur** n'écoute et ne voit que les segments qui lui sont attribués. Il ne peut pas télécharger les projets.
- L'audio n'est accessible qu'après connexion. Seule la documentation est publique.

---

## 4. Les données des comptes

Les comptes sont créés par un administrateur. Il n'y a pas d'inscription libre.

| Donnée | Pourquoi | Où |
|---|---|---|
| Nom d'utilisateur | Se connecter, savoir qui a fait quoi | Fichier des comptes |
| Mot de passe | Se connecter. Seule une empreinte (hachage) est enregistrée : personne, administrateurs compris, ne peut lire le mot de passe | Fichier des comptes |
| Rôle (administrateur ou transcripteur) | Droits d'accès | Fichier des comptes |
| Date de création du compte, date de dernière connexion | Gestion des comptes | Fichier des comptes |
| Auteur et date de chaque enregistrement : `done_by` (qui a terminé le segment), `corrected_by` (qui l'a corrigé ensuite), `updated_by` et `updated_at` (dernière modification) | Suivi du travail, contrôle qualité, attribution des corrections | Fichier d'annotations de chaque projet |
| Segments attribués à chaque compte | Répartition du travail | Fichier d'attribution de chaque projet |
| Journal technique des requêtes (date, adresse demandée, code de réponse) | Diagnostic des erreurs | Journal du serveur |

La plateforme **ne demande pas** d'adresse e-mail, de nom réel, de numéro de téléphone ni de pièce d'identité. **[À COMPLÉTER : si les transcripteurs sont rémunérés ou liés par un contrat, les données correspondantes sont gérées en dehors de la plateforme : préciser par qui.]**

Le nombre de segments terminés et corrigés par chaque compte est visible des administrateurs. Il sert à suivre l'avancement et la qualité, **[À COMPLÉTER : et, le cas échéant, au calcul de la rémunération]**.

---

## 5. Cookies et stockage dans le navigateur

| Nom | Type | Rôle | Durée |
|---|---|---|---|
| `labelin_session` | Cookie | Rester connecté. Indispensable au fonctionnement, il ne contient pas le mot de passe. | 30 jours, ou jusqu'à la déconnexion |
| `labelin.theme`, `labelin.autoplay`, `labelin.langs`, `labelin.lastProject`… | Stockage local du navigateur | Préférences d'affichage et brouillon en cours. Ces données restent sur votre appareil et ne sont pas envoyées au serveur. | Jusqu'à ce que vous les effaciez |

Il n'y a **aucun cookie publicitaire ni outil de mesure d'audience**. Les pages ne chargent aucun script, police ou image depuis un autre site.

---

## 6. Hébergement et transferts

- Les fichiers (audio, transcriptions, comptes) sont stockés sur un **serveur situé à Madagascar** et administré par le responsable du projet.
- L'accès par l'adresse publique `labelin.marindrano.com` passe par **Cloudflare**, un service américain de réseau et de sécurité. Cloudflare transporte le trafic chiffré et peut voir l'adresse IP des visiteurs et les pages demandées. Il ne conserve pas les fichiers du projet.
- **[À COMPLÉTER : autres transferts éventuels, par exemple copies de sauvegarde, envoi du corpus à un partenaire ou à un service de calcul pour l'entraînement des modèles.]**

---

## 7. Durées de conservation

| Données | Durée |
|---|---|
| Audio et transcriptions | **[À COMPLÉTER : par exemple durée de la thèse + N ans, ou conservation à long terme pour un corpus publié]** |
| Comptes | Jusqu'à la fin de la participation au projet, puis suppression du compte. Les noms d'utilisateur restent dans l'historique des segments **[À COMPLÉTER : ou sont remplacés par un identifiant anonyme]**. |
| Journal technique du serveur | **[À COMPLÉTER : par exemple 3 mois]** |
| Copies de sauvegarde | **[À COMPLÉTER]** |

---

## 8. Engagement de confidentialité des transcripteurs

En utilisant la plateforme, chaque transcripteur s'engage à :

- ne pas copier, enregistrer, partager ou publier l'audio ni les transcriptions en dehors de la plateforme ;
- ne pas chercher à identifier ou contacter les personnes entendues ;
- appliquer la règle des données personnelles (balise `[personnel]`, indicateur *données personnelles*, exclusion des contenus sensibles) ;
- ne pas partager son mot de passe ni laisser une session ouverte sur un appareil partagé ;
- signaler sans délai au responsable toute fuite ou tout accès suspect.

Cet engagement continue après la fin de la participation au projet.

---

## 9. Publication du corpus

**[À COMPLÉTER : le corpus sera-t-il publié ? Où (dépôt, plateforme), sous quelle licence, sous quelle forme (audio + texte, ou texte seul) ? Les noms d'utilisateur des transcripteurs seront-ils retirés ou remplacés ?]**

Dans tous les cas, ne sont jamais publiés : les segments exclus, les segments signalés *données personnelles* dont l'audio n'est pas masqué, et les comptes (mots de passe, dates de connexion).

---

## 10. Vos droits

Selon la loi applicable, toute personne concernée peut demander l'**accès** aux données qui la concernent, leur **rectification**, leur **suppression** ou s'**opposer** à leur traitement. Cela vaut pour :

- les **transcripteurs**, pour les données de leur compte et leur nom dans l'historique des segments ;
- les **personnes entendues** dans les enregistrements, qui peuvent demander le retrait d'un passage.

Écrire au contact indiqué en section 1 : **[À COMPLÉTER : adresse e-mail]**. La réponse est donnée dans un délai de **[À COMPLÉTER : par exemple 30 jours]**.

En cas de désaccord, une réclamation peut être adressée à la **Commission Malagasy sur l'Informatique et les Libertés (CMIL)** **[À COMPLÉTER : vérifier l'autorité compétente]**.

---

## 11. Modifications

Toute modification de cette politique change son numéro de version et sa date en haut de page. Les changements importants sont annoncés aux transcripteurs avant d'entrer en vigueur.

- `v0.1` : premier brouillon.
