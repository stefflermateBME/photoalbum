# PhotoAlbum – Fejlesztői dokumentáció

## Projekt összefoglaló

Ez a repository egy többfelhasználós fényképalbum webalkalmazás megoldását tartalmazza, amelyet a PaaS alapú beadandó feladathoz készítettem.
Az alkalmazás célja, hogy a felhasználók képeket tudjanak feltölteni, törölni, listázni és megtekinteni, valamint regisztráció és bejelentkezés után csak jogosult felhasználók férjenek hozzá a módosító műveletekhez.

A megoldást **Django** alapokon, **OpenShift** környezetben futtatva valósítottam meg.
A végleges változat többrétegű, mert:
- a webalkalmazás külön konténerben fut,
- az adatok külön PostgreSQL adatbázisban vannak tárolva (Neon),
- a feltöltött képfájlok külön persistent volume-on (PVC) vannak tárolva.

Ezáltal a megoldás megfelel annak a követelménynek, hogy a végleges rendszer külön adatbázissal működjön, és alkalmas legyen skálázható PaaS környezetben való futtatásra.

## Használt technológiák

- **Backend:** Python, Django
- **Adatbázis:** PostgreSQL (Neon)
- **Fájltárolás:** OpenShift PersistentVolumeClaim
- **Konténerizálás:** Docker
- **PaaS platform:** OpenShift / OKD
- **Build és deploy:** OpenShift BuildConfig + GitHub webhook
- **Routing:** OpenShift Route
- **Kiszolgálás:** konténeren belüli Django alkalmazás 8080-as porton

## Funkcionális követelmények megvalósítása

Az alkalmazás a kiadott feladat követelményeit az alábbi módon teljesíti.

### 1. Fényképek feltöltése és törlése
A bejelentkezett felhasználók képeket tudnak feltölteni az alkalmazásba. A képek törlése szintén csak hitelesített felhasználó számára engedélyezett.

### 2. Képnév és feltöltési dátum
Minden feltöltött képhez tartozik:
- egy név,
- valamint a feltöltés időpontja.

A név maximális hosszát az alkalmazás oldalon korlátoztam, a feltöltési dátum pedig automatikusan rögzítésre kerül.

### 3. Listázás és rendezés
A képek listázhatók:
- név szerint rendezve,
- dátum szerint rendezve.

A listanézetben a metaadatok jelennek meg, így a felhasználó könnyen át tudja tekinteni a feltöltött elemeket.

### 4. Kép megjelenítése
A lista egy elemére kattintva az adott fénykép megtekinthető.

### 5. Felhasználókezelés
Az alkalmazás támogatja a következőket:
- regisztráció,
- bejelentkezés,
- kijelentkezés.

### 6. Jogosultságkezelés
A módosító műveletek, mint a feltöltés és törlés, kizárólag belépett felhasználók számára érhetők el.

## Architektúra

A végleges rendszer három fontos részre bontható:

### 1. Django alkalmazás
Ez kezeli:
- a webes felületet,
- a felhasználókezelést,
- az üzleti logikát,
- a képek metaadatainak kezelését,
- az adatbázis kapcsolatot.

### 2. PostgreSQL adatbázis (Neon)
A strukturált adatok, például:
- felhasználók,
- képek neve,
- feltöltési időpont,
- adatbázis rekordok

nem helyben, hanem egy külső Neon PostgreSQL adatbázisban vannak tárolva.

### 3. Persistent fájltárolás OpenShiftben
A képfájlok nem az adatbázisban vannak, hanem egy PersistentVolumeClaim által biztosított tárhelyen. Ez azért fontos, mert a konténerek újraindulhatnak vagy lecserélődhetnek, de a feltöltött médiatartalomnak meg kell maradnia.

**Összefoglalva:**
- **képfájlok:** PVC-n
- **metaadatok és felhasználói adatok:** Neon PostgreSQL-ben

## OpenShift alapú működés

A projektet OpenShiftben futtattam. A deploy nem csak egy sima konténerindításból áll, hanem több OpenShift erőforrás együttműködéséből.

A repository GitHub-on található, és az OpenShift úgy van beállítva, hogy a kódban történt változások esetén új build induljon.

### OpenShift erőforrások szerepe

#### Deployment
A Deployment felelős az alkalmazás példányainak futtatásáért. Itt van definiálva többek között:
- a konténer image,
- a környezeti változók,
- a csatolt volume-ok,
- a port,
- a rolling update stratégia.

A deploymentben külön beállítottam:
- DATABASE_URL
- DJANGO_SECRET_KEY
- DJANGO_ALLOWED_HOSTS
- DJANGO_MEDIA_ROOT
- DJANGO_STATIC_ROOT

A konténer a 8080-as porton fut, ezt használja a service és a route is.

#### Pod
A Pod az éppen futó konkrét példányt jelenti. A podban látszik, hogy:
- a konténer nem root felhasználóként fut,
- a médiatároló volume csatolva van,
- a static fájlok számára külön mount készült,
- a környezeti változók ténylegesen átadásra kerülnek.

Ez OpenShift szempontból fontos, mert a platform alapértelmezetten szigorúbb biztonsági beállításokkal dolgozik.

#### Service
A Service biztosít belső hálózati elérést a pod felé az OpenShift klaszteren belül. A service a 8080-as portot irányítja át a megfelelő konténerportra.

#### Route
A Route teszi publikusan elérhetővé az alkalmazást. Ez biztosítja a külső URL-t, amin keresztül a webalkalmazás böngészőből elérhető.
A route TLS edge terminationnel van konfigurálva, tehát HTTPS elérés is biztosított.

#### PersistentVolumeClaim
A PersistentVolumeClaim biztosítja a tartós tárhelyet a feltöltött képek számára.
A projektben:
- a képek a PVC-re kerülnek,
- a mount pont: /data/media

Ez megakadályozza, hogy a konténer újraindítása esetén a feltöltött képek elveszjenek.

#### BuildConfig
A BuildConfig végzi a GitHub repository-ból történő buildelést.
A build:
- Git forrásból indul,
- a repository gyökerét használja contextként,
- a Dockerfile alapján készíti el az image-et,
- az elkészült image-et egy OpenShift ImageStreamTag-be tölti fel.

Be van állítva:
- GitHub webhook trigger
- Generic webhook trigger
- ConfigChange trigger

Ez azt jelenti, hogy a GitHubra történő push után az OpenShift automatikusan új buildet tud indítani.

### Kiemelés: a YAML fájlokat OpenShiftben készítettem / kezeltem

A projekt egyik fontos része, hogy a deploy-hoz szükséges YAML erőforrásokat OpenShift környezetben állítottam össze és módosítottam. Ez különösen fontos ennél a beadandónál, mert a cél nem csak egy lokálisan működő program elkészítése volt, hanem egy valódi PaaS környezet használata is.

A használt YAML konfigurációk:
- Deployment
- Pod
- Service
- Route
- PersistentVolumeClaim
- BuildConfig

Ezeket az OpenShift Web Console-ban hoztam létre, illetve ott finomhangoltam. A konfigurációk így nem elméleti példák, hanem a ténylegesen futó alkalmazás infrastruktúráját írják le.

Különösen ezekre kellett figyelnem OpenShift alatt:
- a konténer portjának megfelelő kivezetése,
- a route helyes konfigurálása,
- a médiafájlok tartós tárolása PVC-vel,
- a külső PostgreSQL adatbázis elérhetősége,
- a build automatizálása GitHub webhookkal,
- a Django környezeti változóinak átadása.

## Adattárolási stratégia

A megoldásnál tudatosan különválasztottam a strukturált adatokat és a bináris fájlokat.

### Képek tárolása
A feltöltött képek OpenShift PVC-n vannak tárolva.
Ennek előnyei:
- nem vesznek el pod restart esetén,
- nem a konténer fájlrendszerében maradnak,
- a médiaállományok kezelése elkülönül az alkalmazáskódtól.

### Metaadatok és felhasználói adatok
Az alkalmazás adatai Neon PostgreSQL adatbázisban vannak tárolva.
Ide kerülnek például:
- felhasználói adatok,
- autentikációs információk,
- képek nevei,
- dátumok,
- adatbázis rekordok.

Ez a megoldás megfelel a második beadási rész követelményének, miszerint a végleges változat külön adatbázis-szerverrel működjön.

## Környezeti változók

Az alkalmazás futásához szükséges főbb környezeti változók:
- DATABASE_URL – a Neon PostgreSQL kapcsolati URL-je
- DJANGO_SECRET_KEY – Django titkos kulcs
- DJANGO_ALLOWED_HOSTS – az OpenShift route host neve
- DJANGO_MEDIA_ROOT – médiatárolás helye
- DJANGO_STATIC_ROOT – statikus fájlok helye

### Fontos megjegyzés
Fejlesztői szempontból helyesebb megoldás lenne az érzékeny adatokat nem közvetlenül a deployment YAML-ben tárolni, hanem OpenShift Secret használatával kezelni. A jelenlegi működő konfigurációban a változók environment formában vannak átadva, de továbbfejlesztésként ezt érdemes Secret/ConfigMap alapú megoldásra cserélni.

## Build és automatikus újratelepítés

A projekt GitHub repository-ból épül OpenShiftben.

A folyamat:
1. kód push a GitHub repository-ba,
2. webhook értesíti az OpenShiftet,
3. elindul az új build a BuildConfig alapján,
4. elkészül az új image,
5. az ImageStream frissül,
6. a Deployment trigger miatt az új image automatikusan kitelepül.

Ez biztosítja, hogy a repository és a futó alkalmazás szinkronban maradjon, és a build/deploy folyamat automatizált legyen.
