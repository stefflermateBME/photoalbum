# Photoalbum – végleges megoldás dokumentáció

## Áttekintés

Ez a dokumentum a `photoalbum` alkalmazás futtatási környezetét, architektúráját és telepítési logikáját foglalja össze.

## Választott környezet

| Elem | Megoldás |
|---|---|
| PaaS | Red Hat OKD 4.x (OpenShift Developer Sandbox) |
| Keretrendszer | Python + Django |
| Konténerizálás | Dockerfile + OpenShift BuildConfig |
| Telepítés | OpenShift Deployment (RollingUpdate) |
| Külső adatbázis | Neon Postgres |

## Rétegek és komponensek

### 1) Alkalmazási réteg

- A `photoalbum` Django projekt konténerben fut.
- A futó példányokat `Deployment` erőforrás kezeli és skálázza.
- A feltöltött képek tárolása `MEDIA_ROOT` alatt történik, PVC mounttal (CephFS).
- A statikus fájlokat (`CSS/JS`) a `WhiteNoise` szolgálja ki.
- Build/futás közben a `collectstatic` az állományokat egy `emptyDir` kötetbe gyűjti.

### 2) Adatbázis-réteg

- A `DATABASE_URL` környezeti változó egy Neon Postgres példányra mutat.
- A Neon a klaszteren kívüli, külső szolgáltatásként működik.
- A Django TCP kapcsolaton keresztül éri el, így az alkalmazás- és adatbázisréteg tisztán szétválik.

### 3) Tároló réteg

- Az `media-pvc` CephFS-alapú perzisztens kötet.
- Jelenlegi hozzáférési mód: `ReadWriteOnce` (egyszerre egy node írhatja).
- Több példányos futtatáshoz javasolt `ReadWriteMany`-t támogató storage class, vagy külső objektumtároló.

## CI/CD és telepítés

- A `k8s/03-build.yaml` definiálja az `ImageStream` és `BuildConfig` erőforrásokat.
- A BuildConfig Git forrásból, Docker stratégiával épít image-et.
- A kész image célja: `photoalbum-git:latest` (`ImageStreamTag`).
- A `triggers` mezőben GitHub webhook trigger szerepel, ezért minden push új buildet indíthat.
- A webhook URL a BuildConfig **Webhooks** szekciójából másolható.
- Sikeres build után az ImageStream frissül, és az ImageChange trigger újraindítja/frissíti a Deployment podokat.

## Kapcsolatok

- **Alkalmazás ↔ Adatbázis:** a Django a `postgresql://...` URI alapján kapcsolódik a Neonhoz.
- **Alkalmazás ↔ Tároló:** a képek PVC-n tárolódnak, és `MEDIA_URL` alatt érhetők el.
- **CI ↔ Kód:** GitHub push esemény → webhook → BuildConfig build → új image.
- **Külső elérés:** OpenShift Route irányítja a HTTP(S) forgalmat a Deployment podokra.

## Neon mint külön adatbázis-szerver

A Neon felhőalapú PostgreSQL szolgáltatás. Mivel az alkalmazás URI-n keresztül csatlakozik hozzá, a Neon önálló adatbázisrétegnek tekinthető (ugyanúgy, mint egy dedikált DB szerver). Ez biztosítja a web/app és adatbázis réteg elválasztását, ami megfelel a többrétegű architektúra elvének.

## További megfontolások

### Skálázhatóság

- A `Deployment` replikaszámának növelésével horizontális skálázás érhető el.
- Ehhez a médiafájlok tárolásának több pod számára is írható/olvasható módon elérhetőnek kell lennie (`RWX`, S3/MinIO).

### Webhook jogosultságok

- OpenShift 4.x környezetben a GitHub webhook működéséhez szükség lehet arra, hogy a `system:unauthenticated` csoport rendelkezzen `system:webhook` jogosultsággal a namespace-ben.

### Biztonság

- A webhook secretet és az alkalmazás titkos kulcsait (`Secret`) erős, véletlenszerű értékkel érdemes beállítani.
- A GitHub webhook és az OpenShift BuildConfig titkos kulcsa legyen konzisztens.