# Photoalbum – végleges megoldás dokumentáció

## Projekt áttekintés

A cél egy skálázható, felhőalapú fényképalbum-alkalmazás létrehozása publikus PaaS környezetben.

- Python + Django alapú webalkalmazás
- OpenShift Developer Sandbox klaszteren futtatva
- Felhasználói funkciók: kép feltöltés, listázás (név/dátum), részletnézet
- Beépített felhasználókezelés: regisztráció, belépés, kilépés
- Jogosultság-ellenőrzés a védett műveleteknél

## Tartalomjegyzék

- [Környezet](#környezet)
- [Architektúra és rétegek](#architektúra-és-rétegek)
- [Telepítési lépések összefoglalója](#telepítési-lépések-összefoglalója)
- [Kapcsolatok és biztonsági beállítások](#kapcsolatok-és-biztonsági-beállítások)
- [Neon mint külön adatbázis](#neon-mint-külön-adatbázis)
- [Jövőbeli fejlesztési lehetőségek](#jövőbeli-fejlesztési-lehetőségek)

## Környezet

| Komponens | Leírás |
|---|---|
| PaaS | Red Hat OKD 4 (OpenShift Developer Sandbox) |
| Programnyelv / keretrendszer | Python 3 + Django |
| Tárolótechnológia | Dockerfile alapú build, OpenShift BuildConfig használatával |
| CI/CD | GitHub webhookok által indított OpenShift BuildConfig build-ek |
| Adatbázis | Neon Postgres (felhőalapú, külső adatbázis-szolgáltatás) |
| Persistent storage | CephFS alapú PVC (`ReadWriteMany`) képek és médiatartalom tárolására |
| Deployment stratégia | RollingUpdate (zéró közeli állásidő) |

## Architektúra és rétegek

### 1) Alkalmazási réteg

- A Django webalkalmazás konténerben fut.
- A példányszámot és frissítéseket `Deployment` kezeli (`RollingUpdate`).
- A statikus fájlokat a `WhiteNoise` middleware szolgálja ki.
- A `collectstatic` a statikus tartalmat `emptyDir` kötetbe gyűjti.
- A `MEDIA_ROOT` PVC-re mountolt, ezért a feltöltött képek újraindítás után is megmaradnak.
- A konfiguráció környezeti változókon keresztül érkezik (pl. adatbázis URI, titkos kulcs, allowed hosts).

### 2) Adatbázis-réteg

- A `DATABASE_URL` egy Neon Postgres példányra mutat.
- A Neon menedzselt, külső szolgáltatásként működik (klaszteren kívül).
- A kapcsolat TCP-n keresztül történik, így az app és DB réteg elkülönül.

### 3) Tároló réteg

- A képek tárolása PVC-n történik.
- A korai megoldás `ReadWriteOnce` módot használt.
- A végleges megoldás `ReadWriteMany` (CephFS, `media-pvc-rwx`) hozzáférést biztosít.
- A kötet a podban a `/data/media` útvonalra mountolódik.
- A Django oldalon ezt a `DJANGO_MEDIA_ROOT` változó veszi át.
- Alternatíva: S3/MinIO objektumtároló még jobb horizontális skálázáshoz.

### 4) CI/CD réteg

- Az OpenShift `BuildConfig` és `ImageStream` építi és tárolja az image-et.
- A forrás a GitHub repository `main` ága.
- GitHub webhook trigger minden push esetén új buildet indít.
- Sikeres build után az `ImageStream` `:latest` tag frissül.
- Az `ImageChange` trigger automatikusan frissíti a Deployment podokat.

### 5) Hálózati réteg

- Belső forgalom: `Deployment -> Service` OpenShift DNS használatával.
- Külső forgalom: `Route` HTTPS végponton keresztül.
- Django proxy-kompatibilitás:
  - `USE_X_FORWARDED_HOST`
  - `SECURE_PROXY_SSL_HEADER`

## Telepítési lépések összefoglalója

1. **Fejlesztés helyben**
	- Python virtualenv + Django környezet
	- Lokális tesztelés (akár SQLite alapon)

2. **Konténerizálás**
	- `Dockerfile` állítja össze a futtatási képet
	- Függőségek telepítése: `requirements.txt`
	- `collectstatic` és migrációk a pipeline részeként futnak

3. **Forráskezelés és triggerelés**
	- Kód push a GitHub repóba
	- A beállított BuildConfig webhook automatikusan buildet indít

4. **OpenShift erőforrások**
	- `03-build.yaml`: `ImageStream` + `BuildConfig` webhook triggerrel
	- `Deployment`: konténer futtatás, env változók, volume mountok
	- `Service` + `Route`: belső/külső elérés
	- `PersistentVolumeClaim`: `media-pvc-rwx` (`ReadWriteMany`)

5. **Pipeline ellenőrzés**
	- Build státusz követése BuildConfig logokban
	- Sikeres build után automatikus Deployment frissítés

6. **Skálázás**
	- Replikaszám növelése Deployment szinten
	- Az RWX kötet miatt minden pod ugyanazt a médiatartalmat látja

## Kapcsolatok és biztonsági beállítások

### Adatbázis-kapcsolat

- A `DATABASE_URL` tartalmazza a Neon Postgres URI-t.

### Media storage

- A PVC `media-storage` volume-on keresztül csatlakozik.
- A `DJANGO_MEDIA_ROOT` + `MEDIA_URL` biztosítja a `/media/...` elérhetőséget.

### Webhook jogosultság

- OKD 4 környezetben GitHub webhookhoz szükséges lehet a `system:unauthenticated` csoport `system:webhook` jogosultsága.
- Ez jellemzően `RoleBinding` erőforrással állítható be.

### Titokkezelés

- A GitHub webhook és BuildConfig azonos titkot használjon.
- Erős, véletlenszerű kulcs használata ajánlott.

### Biztonságos HTTP

- A `Route` TLS terminációt végez.
- A Django oldalon a `SECURE_PROXY_SSL_HEADER` biztosítja a proxy mögötti helyes működést.

## Neon mint külön adatbázis

A Neon Postgres szolgáltatás a klaszteren kívül, független hoszton fut. Az alkalmazás TCP kapcsolaton keresztül éri el, ezért az adatbázisréteg fizikailag és logikailag is elkülönül az alkalmazásrétegtől. Ez megfelel a többrétegű architektúra alapelvének.

## Jövőbeli fejlesztési lehetőségek

### 1) Objektumtároló bevezetése

- S3-kompatibilis tárhely (pl. MinIO) a médiához
- Jobb konkurens hozzáférés és rugalmasabb skálázás

### 2) Horizontális autoscaling

- HPA (`Horizontal Pod Autoscaler`) CPU/memória metrikák alapján
- Dinamikus podszám skálázás terheléshez igazítva

### 3) CI/CD bővítése

- Tesztek és linter beépítése a pipeline-ba
- Staging környezet release előtti ellenőrzéshez

## Összegzés

A megoldás egy több rétegű, skálázható felhőalkalmazás, amelyben az alkalmazásréteg, az adatbázisréteg és a tárolóréteg tisztán elválik. A GitHub webhook + OpenShift BuildConfig folyamatos, automatizált build/deploy működést biztosít, míg az RWX storage támogatja a több példányos, üzembiztos futtatást.