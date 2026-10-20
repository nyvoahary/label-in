# Convention de transcription PROVA-MG

**Version : CONVENTION_VERSION v1.4**
Parole malgache, avec code-switching malgache-français.

Ce guide s'adresse aux transcripteurs. Chaque règle est accompagnée d'exemples et de remarques. En cas de doute, cocher l'indicateur adapté plutôt que deviner.

---

## Sommaire

1. Verbatim
2. Orthographe malgache
3. Code-switching
4. Nombres
5. Majuscules, ponctuation, sigles
6. Balises
7. Pièges du brouillon Whisper
8. Segmentation
9. Paramètres par segment
10. Contrôle qualité
11. Aide-mémoire

---

## 1. Verbatim

On écrit **ce qui est dit**, pas ce qui aurait dû être dit. On ne corrige ni la grammaire, ni les répétitions, ni les hésitations.

| Cas | Correct | Incorrect |
|---|---|---|
| Répétition | `nandeha nandeha tany an-tsena izy` | `nandeha tany an-tsena izy` |
| Faux départ (mot coupé + tiret) | `mand- mandeha aho` | `mandeha aho` |
| Autocorrection | `rahampitso, tsia, afak'omaly izy no tonga` | `afak'omaly izy no tonga` |
| Ordre des nombres non standard | Le locuteur dit "roa arivo sy enina amby roapolo" : on garde cet ordre | Remettre l'ordre classique "enina amby roapolo sy roa arivo" |

> **Remarque.** Le modèle doit apprendre la parole réelle. Si on "nettoie" la transcription, le modèle apprend à entendre des mots qui n'ont pas été prononcés, et il sera pénalisé en évaluation sur de la parole spontanée.

---

## 2. Orthographe malgache

On applique l'orthographe officielle du malgache.

| Cas | Correct | Incorrect |
|---|---|---|
| Son [u] écrit *o* | `volona` | `vuluna` |
| *-y* en fin de mot | `misy`, `vary` | `misi`, `vari` |
| *-i* à l'intérieur du mot | `fitiavana` | `fytiavana` |
| Pas de c, q, u, w, x dans un mot malgache | `kafe` | `cafe` (sauf si prononcé à la française, voir règle 3) |

### Dialectes : on garde le mot dialectal

On **ne convertit pas** vers le malgache officiel (merina). La variété se renseigne dans le champ *Dialecte*.

| Locuteur | Correct | Incorrect |
|---|---|---|
| Locuteur du Sud | `zaho tsy mahay` | `aho tsy mahay` |

> **Remarque.** Convertir un dialecte en merina efface précisément l'information que la thèse veut modéliser (variation dialectale). Un mot dialectal correctement transcrit vaut plus qu'un mot "standardisé".

### Apostrophes et tirets

**Une seule apostrophe autorisée : l'apostrophe droite `'`.** L'apostrophe typographique `’` (souvent insérée automatiquement par Word ou le téléphone) est interdite.

| Cas | Correct | Incorrect |
|---|---|---|
| Élision avec apostrophe | `an'ny`, `tamin'ny`, `afak'omaly`, `nataon'i Rabe` | `anny`, `an ny`, `an’ny` |
| Préfixe de lieu avec tiret | `an-tsena`, `an-trano` | `antsena`, `an tsena` |
| Redoublement : un seul mot, sans tiret | `tsaratsara`, `kelikely` | `tsara-tsara`, `tsara tsara` |

> **Remarque.** Pour la machine, `an'ny` et `an’ny` sont deux mots différents. Une seule apostrophe de travers suffit à créer un faux mot dans le vocabulaire et une fausse erreur dans le calcul du WER. L'application refuse donc `’` à l'enregistrement.

En cas de doute sur la graphie d'un mot composé : consulter le lexique partagé, sinon cocher *transcription incertaine*.

---

## 3. Code-switching

### 3.1 Règle principale : la prononciation décide

- Prononcé avec la **phonologie malgache** : orthographe **malgache**.
- Prononcé **à la française** : orthographe **française complète, avec accents**.

| Prononcé | Correct |
|---|---|
| [telefaunina] | `telefaonina` |
| [telefɔn] | `téléphone` |
| [seza] | `seza` |
| [ʃɛz] | `chaise` |

> **Remarque.** Le même mot d'origine française peut donc s'écrire de deux façons selon le locuteur. C'est voulu : on transcrit ce qui est prononcé, pas l'étymologie.

### 3.2 Emprunts intégrés courants (toujours en malgache)

`latabatra` (la table), `sekoly` (école), `lakozia` (la cuisine), `fety` (fête), `kafe` (café)

### 3.3 Commutation à l'intérieur d'une phrase

Dit : *"Tsy afaka ny réunion aho fa misy rendez-vous chez le médecin"*

| | Transcription |
|---|---|
| Correct | `Tsy afaka ny réunion aho fa misy rendez-vous chez le médecin.` |
| Incorrect | `Tsy afaka ny reniona aho fa misy randevo se le medesina.` |

### 3.4 Commutation entre deux phrases

`Efa vita ny asa. Bon, on se voit demain alors.`

### 3.5 Mots hybrides (affixe malgache + racine française)

La racine reste en orthographe française. L'affixe malgache est relié par un **tiret**.

| Correct | Incorrect |
|---|---|
| `mi-confirmer` | `mikonfirmé` |
| `voa-valider` | `voavalidé` |
| `nanao réservation` | `nanao rezervasiona` |

> **Remarque.** C'est le cas le plus fréquent en parole spontanée urbaine. Le tiret permet ensuite de séparer automatiquement la partie malgache et la partie française.

### 3.6 Cas ambigu

Exemple : on entend [buati]. Est-ce `boaty` ou `boîte` ?

- Cocher l'indicateur **emprunt ambigu**.
- Écrire la forme qui semble la plus proche.
- Le mot est ajouté au **lexique partagé**, où la décision est prise une fois pour toute l'équipe.

> **Remarque.** Ne jamais trancher seul un cas ambigu de façon différente d'un collègue. L'incohérence entre transcripteurs est plus nuisible qu'une erreur cohérente.

---

## 4. Nombres

Toujours **en toutes lettres**, dans **la langue réellement parlée**.

| Dit | Correct | Incorrect |
|---|---|---|
| Montant en malgache | `telo arivo ariary` | `3000 Ar` |
| Heure en français (très fréquent) | `amin'ny huit heures` | `amin'ny 8h` / `amin'ny valo ora` |
| Numéro de téléphone d'une personne privée | `[personnel]` (voir règle 6.1) | `zero telo efatra...` ou `034...` |
| Numéro public (standard d'une radio, d'une institution) | `zero telo efatra...` | `034...` |
| Verset biblique | Le lecteur dit *"Jaona toko fahatelo, andininy fahenina ambin'ny folo"* : on écrit exactement ces mots | `Jaona 3:16` |
| Date mixte | `ny vingt-cinq octobre` | `ny 25/10` |

> **Remarque.** La conversion en chiffres se fait plus tard, automatiquement (normalisation). Si le transcripteur écrit "8h", on ne sait plus si le locuteur a dit "huit heures" ou "valo ora". L'information est perdue.

---

## 5. Majuscules, ponctuation, sigles

- **Majuscule** : début de phrase, noms propres.
- **Ponctuation autorisée** : `.` `,` `?` uniquement.
- **Sigles** : en capitales, sans points.

| Cas | Correct |
|---|---|
| Noms propres | `Nandeha tany Toamasina i Rakoto omaly.` |
| Question | `Ho avy ve ianao?` |
| Sigle prononcé comme un mot | `JIRAMA` |
| Sigle épelé | `TVA` (pas `T.V.A.`, pas `té vé a`) |
| Titre dit en malgache | `dokotera Rabe` (pas `Dr Rabe`) |
| Titre dit en français | `docteur Rabe` |

### 5.1 Majuscule et point : la phrase décide, pas le segment

La majuscule marque le **début réel d'une phrase**, pas le début du segment. Même logique pour le point final.

- Le segment commence au milieu d'une phrase : **pas de majuscule**.
- Le segment s'arrête au milieu d'une phrase : **pas de point final**.
- Un nom propre garde toujours sa majuscule, où qu'il soit.

Phrase dite : *"Rehefa tonga tany Toamasina izahay dia nivory tao amin'ny fiangonana izahay."*, coupée en deux segments à une pause.

| Segment | Correct | Incorrect |
|---|---|---|
| 1 | `Rehefa tonga tany Toamasina izahay` | `Rehefa tonga tany Toamasina izahay.` |
| 2 | `dia nivory tao amin'ny fiangonana izahay.` | `Dia nivory tao amin'ny fiangonana izahay.` |

> **Remarque.** Si chaque segment commence par une majuscule, le modèle associe la majuscule au début de l'audio au lieu du début de phrase. En production, il mettra des majuscules et des points au milieu des phrases. Pour le WER, ça ne change rien (la normalisation retire casse et ponctuation), mais c'est la qualité du texte produit qui en souffre.

---

## 6. Balises

Liste **fermée** : n'utiliser que ces balises.

| Balise | Usage | Exemple |
|---|---|---|
| `[euh]` | hésitation (euh, eh, hmm) | `Ny fivoriana [euh] hatao amin'ny alarobia.` |
| `[rire]` | rire | `Tsy mino an'izany aho [rire].` |
| `[bruit]` | bruit ponctuel | `Dia lasa izy [bruit] tsy niverina intsony.` |
| `[inaudible]` | passage incompréhensible | `Hoy izy hoe [inaudible] dia lasa.` |
| `((mot))` | mot entendu mais incertain | `Nonina tany ((Ambohimanarina)) izy.` |
| `[personnel]` | donnée personnelle remplacée (règle 6.1) | `Antsoy amin'ny [personnel] aho.` |

> **Remarque.** `[inaudible]` signifie : ne pas deviner. Un mot inventé est pire qu'un trou signalé, car le modèle apprend un faux lien entre le son et le texte.

### 6.1 Données personnelles

Une information qui permet d'identifier ou de contacter **une personne privée** est remplacée par `[personnel]`, et l'indicateur *données personnelles* est coché.

| Type | Dit | Transcription |
|---|---|---|
| Téléphone | *"Ny laharako dia zero telo efatra roa..."* | `Ny laharako dia [personnel].` |
| Adresse | *"Monina ao amin'ny lot IVG 123 Ambohipo aho"* | `Monina ao amin'ny [personnel] aho.` |
| Nom complet d'un particulier | Un auditeur cite sa voisine par son nom complet | `[personnel]` |
| Numéro d'identité, de compte | *"Ny kaontiko dia..."* | `[personnel]` |

**On ne remplace pas :**
- les personnalités publiques dans leur rôle public : pasteur à l'antenne, ministre, présentateur, artiste ;
- les lieux généraux : `Toamasina`, `Ambohipo` (sans adresse précise) ;
- les numéros publics : standard d'une radio, d'une institution.

Un segment entier sur un sujet sensible concernant une personne privée identifiable (santé, conflit familial, mineur) : région *Exclu*, raison *contenu sensible*.

> **Remarque.** Ces segments sont **exclus de l'entraînement** et de toute publication tant que l'audio correspondant n'a pas été masqué. Le corpus a vocation à être ouvert à la communauté : un numéro de téléphone transcrit aujourd'hui serait publié demain.

---

## 7. Pièges du brouillon Whisper

Le brouillon automatique fait gagner du temps, mais il doit être **relu mot à mot**. Jamais validé tel quel.

### 7.1 Traduction du français

| Audio | Brouillon Whisper | Correction |
|---|---|---|
| *"misy réunion"* | `misy fivoriana` | `misy réunion` |

### 7.2 Malgachisation

| Audio | Brouillon Whisper | Correction |
|---|---|---|
| *"réunion"* (prononcé à la française) | `reniona` | `réunion` |

### 7.3 Hallucination sur silence ou musique

| Audio | Brouillon Whisper | Correction |
|---|---|---|
| 5 s de musique, aucune parole | `Misaotra anareo nijery.` | Supprimer le texte, région *Exclu* |

### 7.4 Boucle

#### Ce qu'est une boucle

Whisper génère le texte **mot par mot**, chaque mot étant prédit à partir des précédents. Quand l'audio devient difficile (silence, musique, applaudissements, voix lointaine), le modèle n'a plus d'indice acoustique fiable. Il se rabat sur ce qu'il vient d'écrire, et la suite la plus probable devient la même phrase. Il se met à se recopier.

**Exemple**

- Audio réel : *"Hivory amin'ny alahady ny fiangonana"* puis 10 s d'applaudissements.
- Brouillon Whisper :
  `Hivory amin'ny alahady ny fiangonana. Hivory amin'ny alahady ny fiangonana. Hivory amin'ny alahady ny fiangonana. Hivory amin'ny alahady ny fiangonana.`
- Correct : `Hivory amin'ny alahady ny fiangonana.` puis les applaudissements en région *Exclu* (ou `[bruit]` s'ils sont courts).

> **Remarque.** Les boucles sont plus fréquentes en malgache qu'en anglais : le modèle est moins sûr de lui en malgache, donc il décroche plus vite de l'audio.

#### Boucle ou vraie répétition ?

La règle 1 (verbatim) impose de garder les vraies répétitions. Il faut donc distinguer :

| Indice | Vraie répétition | Boucle Whisper |
|---|---|---|
| À l'écoute | On entend chaque occurrence | On n'entend qu'une fois (ou rien) |
| Contenu | `Amena, amena, amena!` (l'assemblée répond) | Phrase longue copiée à l'identique |
| Position | Pendant la parole | Sur silence, musique, fin de segment |
| Nombre | Plausible (2 ou 3) | Souvent excessif |

**Le seul juge est l'oreille.** En cas de doute, réécouter la zone et compter les occurrences réellement prononcées.

#### Pourquoi c'est grave

1. Si une boucle passe dans les données d'entraînement, le modèle **apprend à boucler**, puisqu'on lui a montré que c'était la bonne réponse.
2. En évaluation, chaque mot inventé compte comme une **insertion** : le taux d'erreur grimpe artificiellement, parfois au-delà de 100 % sur un segment.

> **Remarque.** Les segments où une boucle est probable sont signalés automatiquement sur la plateforme (voir Annexe technique). Ils sont à relire en priorité, mais une boucle peut aussi apparaître dans un segment non signalé.

---

## 8. Segmentation

- **Un seul locuteur** par segment.
- Durée **entre 2 et 30 secondes** (exception : réponse courte avec contenu, voir 8.2).
- Couper sur une **pause naturelle**, jamais au milieu d'un mot.

| Situation | Action |
|---|---|
| Monologue de 45 s | Couper en 2 ou 3 segments aux pauses |
| Dialogue A puis B | Un segment par tour de parole |
| A et B parlent en même temps | Segments séparés + indicateur *chevauchement de voix* |
| Cantique pendant un culte | Région *Exclu*, raison *chant / musique* |

> **Remarque.** La limite de 30 secondes vient de Whisper, qui traite l'audio par fenêtres de 30 secondes. Un segment plus long serait coupé arbitrairement à l'entraînement.

### 8.1 Deux locuteurs de dialectes différents qui alternent

Exemple : podcast de 18 s. L'animateur (merina) pose une question, l'invité (betsimisaraka) répond.

- 0 à 9 s : animateur
- 9 à 18 s : invité

On **coupe au changement de tour**, sur la pause entre les deux.

| Segment | Locuteur | Dialecte | Registre |
|---|---|---|---|
| 0 à 9 s | `S1` (animateur) | `officiel (merina standard)` | `spontané` |
| 9 à 18 s | `S2` (invité) | `betsimisaraka` | `spontané` |

> **Remarque.** Un segment contenant les deux voix ne peut pas recevoir un seul dialecte correct. Il serait faux pour la moitié de son contenu.

### 8.2 Réponse très courte (moins de 2 s)

Exemple : l'animateur parle 12 s, l'invité dit *"Eny"* (1 s), l'animateur reprend.

| Cas | Exemple | Action |
|---|---|---|
| Acquiescement sans contenu | `Eny`, `Ie`, `Hmm` | Pas de segment. On le laisse de côté. |
| Réponse courte avec contenu | `Tsia, tsy marina izany.` | Segment à part, même sous 2 s. |

Si l'acquiescement chevauche la voix de l'animateur, on ne le transcrit pas dans le segment de l'animateur.

> **Remarque.** Un acquiescement isolé n'apporte presque rien au modèle, alors qu'une réponse avec contenu contient du vocabulaire réel. On garde donc la seconde malgré sa durée.

### 8.3 Les deux parlent en même temps

- Deux segments séparés, indicateur *chevauchement de voix* sur les deux.
- Si le chevauchement rend une des voix incompréhensible, cette partie passe en région *Exclu*, raison *trop de chevauchement*.

| Situation | Action |
|---|---|
| L'invité commence sa phrase pendant les 2 dernières secondes de l'animateur, les deux restent compréhensibles | Deux segments + *chevauchement de voix* |
| Les deux parlent fort en même temps pendant 5 s | Ces 5 s en *Exclu* |

### 8.4 Un locuteur qui change de dialecte

Les locuteurs s'adaptent souvent à leur interlocuteur. Un invité betsimisaraka face à un animateur merina peut parler surtout en malgache officiel, puis revenir à son dialecte quand il est plus détendu.

**Règle : le champ Dialecte décrit ce qu'on entend dans le segment, pas l'origine du locuteur.**

| Segment | Ce qu'on entend | Locuteur | Dialecte |
|---|---|---|---|
| Début de l'interview | Formes standard | `S2` | `officiel (merina standard)` |
| Plus tard, en racontant un souvenir d'enfance | Formes dialectales | `S2` | `betsimisaraka` |

Le locuteur reste `S2` dans les deux cas : c'est ce qui garde le lien avec la personne.

> **Remarque.** Ces cas sont précieux pour la thèse. Une même voix qui produit deux variétés permet au modèle de distinguer l'identité du locuteur et le dialecte, deux choses qui sont sinon toujours confondues.

### 8.5 Plusieurs locuteurs dans un même segment

**Principe : on ne mentionne jamais deux locuteurs dans le même segment. On les sépare.**

#### Cas normal : séparable, donc deux régions

Sur la forme d'onde, on trace **deux régions** au lieu d'une. Chaque région a ses propres champs.

Audio : *"Ho avy ve ianao rahampitso?"* (S1) puis *"Eny, ho avy aho amin'ny maraina."* (S2)

| Région | Transcription | Locuteur |
|---|---|---|
| 1 | `Ho avy ve ianao rahampitso?` | `S1` |
| 2 | `Eny, ho avy aho amin'ny maraina.` | `S2` |

Aucune mention du locuteur dans le texte : c'est le champ **Locuteur** qui porte l'information.

#### Cas exceptionnel : inséparable, donc une région avec balises

Échange très rapide, tours de moins d'une seconde :
*"Ho avy ve ianao?" "Eny." "Rahoviana?" "Rahampitso."*

Découper en quatre régions minuscules n'a pas de sens. On garde **une seule région** :

| Champ | Valeur |
|---|---|
| Transcription | `[S1] Ho avy ve ianao? [S2] Eny. [S1] Rahoviana? [S2] Rahampitso.` |
| Locuteur | `S1+S2` |
| Dialecte | celui des deux s'il est identique, sinon `plusieurs` |
| Indicateurs | `plusieurs locuteurs` |

Règles d'écriture des balises :
- Balise `[S1]`, `[S2]`... **avant chaque tour de parole**, y compris le premier.
- Mêmes identifiants que dans le champ Locuteur des autres segments de la source.
- Ordre chronologique. Si deux tours se superposent légèrement, celui qui commence en premier est écrit en premier.

Si les voix se superposent au point d'être incompréhensibles : région *Exclu*, raison *trop de chevauchement*.

| Situation | Action |
|---|---|
| Tours de plus de 2 s, pause entre eux | Deux régions (cas normal) |
| Échange rapide, tours de moins d'une seconde, voix compréhensibles | Une région, balises `[S1]` `[S2]` |
| Voix superposées et incompréhensibles | *Exclu* |

> **Remarque.** Les balises `[S1]`, `[S2]` ne doivent jamais arriver dans les données d'entraînement : le modèle apprendrait à les écrire. Ces segments sont donc **exclus de l'entraînement par défaut** et gardés pour un test de robustesse multi-locuteurs. C'est pourquoi on n'utilise cette solution qu'en dernier recours.

### 8.6 Pause sans changement de locuteur

Une pause seule n'oblige pas à couper. On coupe seulement si une raison l'impose.

| Situation | Action |
|---|---|
| Pause courte (moins de 2 s), segment de moins de 30 s | **On ne coupe pas.** La pause reste dans le segment, rien n'est écrit. |
| Pause longue (2 s ou plus) | **On coupe.** Le silence reste hors des deux segments. |
| Le segment approche 30 s | **On coupe** sur la meilleure pause, de préférence une fin de phrase. |
| Pause remplie (*euh*, *eh*, *hmm*) | Ce n'est pas un silence : `[euh]`, on ne coupe pas. |

**Pause courte : un seul segment**
Dit : *"Nandeha tany an-tsena aho omaly"* (pause d'une seconde) *"ary nividy vary."*
→ `Nandeha tany an-tsena aho omaly ary nividy vary.`

**Pause longue : on coupe**
Un prédicateur dit *"Ary hoy Jesoa."*, s'arrête 4 s, puis reprend.

| Segment | Transcription |
|---|---|
| 1 | `Ary hoy Jesoa.` |
| silence de 4 s | hors segment |
| 2 | `Izaho no lalana sy fahamarinana ary fiainana.` |

Les deux segments gardent le même locuteur (`S1`) et les mêmes paramètres.

**Monologue de 50 s avec plusieurs petites pauses**
On coupe une fois, vers 25 à 30 s, sur la pause qui tombe en fin de phrase. Pas à chaque pause.

> **Remarque.** Couper à chaque pause produit des segments trop courts (peu de contexte pour le modèle) et des phrases cassées (règle 5.1). À l'inverse, un long silence laissé dans un segment est l'endroit où Whisper hallucine ou boucle (règle 7.4). Les seuils de 2 s et 30 s sont à valider sur les premières heures annotées.

---

## 9. Paramètres par segment

### Langue (obligatoire)

| Valeur | Exemple |
|---|---|
| `mg` | *"Mandeha any an-tsena aho."* |
| `fr` | *"Je vous remercie de votre attention."* |
| `mixte` | *"Tsy afaka ny réunion aho."* (un seul mot français suffit) |
| `autre` | Segment entièrement dans une autre langue : *"Thank you so much."* |

> **Remarque.** Le marquage `mixte` est essentiel : les segments mixtes sont rares mais ce sont eux que le modèle rate le plus. On les sur-représente à l'entraînement grâce à ce champ.

### Dialecte (obligatoire)

| Valeur | Indice typique |
|---|---|
| `officiel (merina standard)` | Présentateur de journal, lecture officielle |
| Variété régionale | Mots ou formes dialectales (ex. `zaho` au Sud), intonation régionale |
| `autre / incertain` | Aucun indice clair |
| `plusieurs` | Segment à plusieurs locuteurs de dialectes différents (cas 8.5 uniquement) |

> **Remarque.** Ne pas forcer. Un `incertain` honnête est préférable à une variété devinée. Le dialecte se juge segment par segment, d'après ce qui est entendu, pas d'après l'origine connue du locuteur (voir 8.4).

### Registre (obligatoire)

| Valeur | Exemples |
|---|---|
| `lu` | Journal télévisé, lecture biblique |
| `semi-préparé` | Prêche, kabary, discours officiel |
| `spontané` | Interview de rue, conversation, appel téléphonique |

### Qualité audio (obligatoire)

| Valeur | Exemples |
|---|---|
| `propre` | Studio, podcast |
| `bruit léger` | Ventilateur, salle calme |
| `bruit fort` | Marché, taxi-be |
| `musique de fond` | Prêche avec orgue derrière |

### Locuteur

Identifiant par source. Exemple dans une vidéo de culte : `S1` = pasteur, `S2` = lecteur, `S3` = annonceur. Le même pasteur dans une autre vidéo de la même chaîne garde `S1` s'il est identifiable.

> **Remarque.** Ce champ empêche qu'une même voix se retrouve à la fois dans les données d'entraînement et dans le test. Sinon le modèle paraît meilleur qu'il ne l'est.

### Indicateurs (facultatifs, plusieurs possibles)

| Indicateur | Quand le cocher | Exemple |
|---|---|---|
| chevauchement de voix | Deux voix simultanées | Interruption pendant une interview |
| transcription incertaine | Au moins un `((mot))` dans le segment | `((Ambohimanarina))` |
| nom propre à vérifier | Nom de lieu ou de personne douteux | `((Andrianampoinimerina))` |
| emprunt ambigu | Cas de la règle 3.6 | `boaty` / `boîte` |
| plusieurs locuteurs | Région inséparable avec balises (cas 8.5) | `[S1] Rahoviana? [S2] Rahampitso.` |
| données personnelles | Au moins un `[personnel]` dans le segment (règle 6.1) | `Ny laharako dia [personnel].` |

### Région Exclu : raisons

| Raison | Exemple |
|---|---|
| inaudible | Micro saturé, parole incompréhensible |
| chant / musique | Cantique, intermède musical |
| autre langue | Long passage en anglais |
| trop de chevauchement | Plusieurs personnes parlent en même temps |
| contenu sensible | Sujet sensible concernant une personne privée identifiable (règle 6.1) |

---

## 10. Contrôle qualité

### Double transcription

Un échantillon de segments est transcrit par deux personnes, sans qu'elles voient le travail de l'autre. L'écart entre les deux mesure la fiabilité de la convention.

**Exemple de désaccord**

- Transcripteur A : `nanao réunion`
- Transcripteur B : `nanao fivoriana`
- À l'écoute, le locuteur a dit "réunion". B a appliqué une habitude, pas la règle 3.
- Si les deux avaient raison selon la règle, c'est la règle qui est floue : on la précise.

> **Remarque.** Le désaccord entre deux humains donne le plafond réaliste du modèle. Si deux transcripteurs ne s'accordent pas sur un passage, on ne peut pas exiger du modèle qu'il fasse mieux.

### Versionnement

Chaque annotation porte la version de la convention.

- `v1.0` : convention initiale.
- `v1.1` : ajout de la règle du tiret pour les mots hybrides (`mi-confirmer`). Les annotations `v1.0` contenant `mikonfirmé` sont repérables et corrigeables automatiquement.
- `v1.2` : ajout des règles 8.1 à 8.4 (alternance de locuteurs de dialectes différents, réponses courtes, chevauchement, changement de dialecte d'un même locuteur).
- `v1.3` : ajout de la règle 8.5 (plusieurs locuteurs dans un segment), valeur `plusieurs` pour le dialecte, indicateur `plusieurs locuteurs`.
- `v1.4` : apostrophes et tirets (règle 2), versets et numéros (règle 4), majuscule selon la phrase (5.1), données personnelles et balise `[personnel]` (6.1), pause sans changement de locuteur (8.6), raison d'exclusion *contenu sensible*.

### Lexique partagé

Emprunts ambigus et noms propres, avec la graphie retenue. Versionné avec la convention. À consulter avant de cocher *emprunt ambigu* : la réponse y est peut-être déjà.

---

## 11. Aide-mémoire

| Question | Réponse |
|---|---|
| Le locuteur se répète ? | On garde. |
| Mot dialectal ? | On garde, on coche le dialecte. |
| Mot français prononcé à la française ? | Orthographe française avec accents. |
| Mot français prononcé à la malgache ? | Orthographe malgache. |
| Affixe malgache + mot français ? | Tiret : `mi-confirmer`. |
| Un nombre ? | En lettres, dans la langue parlée. |
| Je n'entends pas ? | `[inaudible]`. Jamais deviner. |
| J'entends mais je doute ? | `((mot))` + indicateur *incertain*. |
| Whisper répète une phrase ? | Réécouter, garder seulement ce qui est dit. |
| Musique ou chant ? | Région *Exclu*. |
| Deux locuteurs dans le segment ? | Couper au changement de tour. |
| *"Eny"* isolé de l'interlocuteur ? | Pas de segment. |
| Réponse courte avec contenu ? | Segment à part, même sous 2 s. |
| Le locuteur change de dialecte ? | Dialecte selon ce qu'on entend, même `S`. |
| Échange trop rapide pour couper ? | Une région, `[S1] ... [S2] ...`, Locuteur `S1+S2`. |
| Apostrophe ? | Toujours `'`, jamais `’`. |
| Segment commencé au milieu d'une phrase ? | Pas de majuscule. Fini au milieu : pas de point. |
| Verset biblique ? | En lettres, tel que lu. |
| Numéro ou adresse d'un particulier ? | `[personnel]` + indicateur *données personnelles*. |
| Pause sans changement de locuteur ? | Moins de 2 s : on garde. 2 s ou plus : on coupe. |
| Cas non prévu ? | Indicateur + signaler au responsable. |

---

## Annexe technique (équipe pipeline)

Mesures prises **avant** la transcription humaine pour réduire les boucles et hallucinations du brouillon Whisper :

- **VAD avant Whisper** (ex. Silero VAD) : silences et musique retirés, Whisper ne reçoit que de la parole.
- **Diarisation avant Whisper** (ex. pyannote) : l'audio est pré-découpé aux changements de locuteur. Whisper ne sépare pas les voix, donc sans diarisation son brouillon enchaîne les tours. Les transcripteurs ajustent alors les frontières au lieu de les chercher.
- `condition_on_previous_text=False` : une boucle dans une fenêtre de 30 s ne contamine pas la suivante.
- `compression_ratio_threshold` (2.4 par défaut) : un texte très répétitif se compresse anormalement bien, ce qui déclenche un nouveau décodage.
- `no_speech_threshold` : supprime la sortie quand le modèle estime qu'il n'y a pas de parole.
- **Signalement automatique** : taux de compression gzip calculé pour chaque brouillon, segments suspects marqués pour relecture prioritaire.

Mesures à l'export :

- Segments avec `[personnel]` : exclus de l'entraînement et de toute publication tant que l'audio n'est pas masqué (bip ou silence sur la zone).
- Segments avec balises `[S1]`, `[S2]` : exclus de l'entraînement, conservés pour le test multi-locuteurs.
- Chaque annotation exportée porte `convention_version` et `norm_version`.
