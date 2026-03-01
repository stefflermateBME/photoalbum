# Photoalbum – részletes projektleírás

Ez a repository egy Django-alapú webalkalmazás, amely képek feltöltését, listázását, megtekintését és (tulajdonos által) törlését valósítja meg.

A dokumentáció célja, hogy **logikai sorrendben**, végigvezesse:
- a kérésfeldolgozás útját,
- az alkalmazás rétegeit,
- a fájlok és mappák szerepét,
- a lokális futtatás és az OpenShift/Kubernetes telepítés menetét.

---

## 1. Gyors áttekintés
 
 
### Technológiai stack
- Backend: `Django 5`
- App szerver (konténerben): `gunicorn`
- Képfeldolgozás/feltöltés: `Pillow` + Django `ImageField`
- Adatbázis: `PostgreSQL` (alapértelmezett célkörnyezet), `DATABASE_URL` alapján
- Statikus fájl kiszolgálás: `WhiteNoise`
- Konténer: `Docker`
- Platform: `OpenShift`/Kubernetes (BuildConfig + Knative Service + PVC)

### Fő funkciók
- Kép listaoldal (publikus)
- Kép részletoldal (publikus)
- Kép feltöltés (bejelentkezett felhasználónak)
- Kép törlés (csak saját képet, bejelentkezve)
- Regisztráció / bejelentkezés / kijelentkezés

---

## 2. Logikai működés – kérés útja elejétől a válaszig

### 2.1 Indulási pont
1. A processz a `manage.py` vagy `gunicorn config.wsgi:application` indítással startol.
2. A Django a `config.settings` modulból tölti be a konfigurációt.
3. A `config.urls` modulban összeáll a globális URL-routing tábla.

### 2.2 URL-routing
- `config/urls.py` továbbítja a gyökér (`/`) útvonalat az `album.urls`-ra.
- A beépített auth URL-ek (`/accounts/`) a Django auth nézeteire mutatnak.
- A `/media/...` útvonal kiszolgálása explicit `serve` hívással történik.

### 2.3 View végrehajtás
Az `album/views.py` egy-egy függvény-alapú nézettel kezeli a route-okat:
- `photo_list`: lekérdezi az összes képet, rendez (`sort=date|name`), renderel.
- `photo_detail`: egy képet tölt be PK alapján.
- `photo_upload`: form validáció + fájlfeltöltés + owner beállítás.
- `photo_delete`: jogosultságellenőrzés (owner), POST-ra törlés.
- `signup`: felhasználó létrehozás és automatikus beléptetés.

### 2.4 Modell és adatbázis
- A `Photo` modell (`album/models.py`) tárolja:
  - `owner` (ForeignKey userre)
  - `name` (max 40)
  - `image` (`upload_to="photos/"`)
  - `uploaded_at`
- A migration (`album/migrations/0001_initial.py`) hozza létre a táblát.

### 2.5 Template renderelés
- A view-k a `templates/` könyvtárból dolgoznak.
- A `base.html` adja a közös fejléc/nav struktúrát.
- Oldalspecifikus template-ek az `album/` és `registration/` mappában vannak.

### 2.6 Response és statikus/média tartalom
- Dinamikus HTML-t Django ad vissza.
- Statikus fájlokat WhiteNoise szolgál ki (`STATIC_ROOT`).
- Feltöltött képeket a Django `/media/...` útvonalon adja vissza (`MEDIA_ROOT`).

---

## 3. Könyvtárstruktúra és felelősségek

## 3.1 Projekt gyökér
- `manage.py`: Django menedzsment parancsok belépési pontja.
- `requirements.txt`: Python függőségek.
- `Dockerfile`: konténer build és futtatás.
- `db.sqlite3`: jelenlegi workspace-ben lévő sqlite fájl (ha erre mutat a `DATABASE_URL`).

## 3.2 `config/` – projekt-szintű konfiguráció
- `settings.py`
  - `.env` betöltés (`python-dotenv`)
  - `DATABASE_URL` alapú DB-konfiguráció (`dj-database-url`)
  - `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
  - static/media beállítások
  - production cookie/security opciók
- `urls.py`
  - admin route
  - app include (`album.urls`)
  - auth include (`django.contrib.auth.urls`)
  - `/media/` kiszolgálás
- `wsgi.py`: WSGI entrypoint (gunicorn ezt használja)
- `asgi.py`: ASGI entrypoint

## 3.3 `album/` – üzleti logika (aktív app)
- `models.py`: `Photo` domain modell.
- `forms.py`: `PhotoUploadForm` (`name`, `image`).
- `views.py`: fő alkalmazásfolyamatok (lista/részlet/feltöltés/törlés/signup).
- `urls.py`: app route-definíciók.
- `admin.py`: `Photo` adminregisztráció listaszűrőkkel.
- `migrations/`: DB séma evolúció.

## 3.4 `templates/` – megjelenítési réteg
- `base.html`: közös layout + auth függő menü.
- `album/photo_list.html`: lista + rendezés linkek.
- `album/photo_detail.html`: részlet + kép megjelenítés.
- `album/photo_upload.html`: multipart upload form.
- `album/photo_confirm_delete.html`: megerősítéses törlés.
- `registration/login.html`: belépési űrlap.
- `registration/signup.html`: regisztrációs űrlap.

## 3.5 `k8s/` – OpenShift/Kubernetes telepítési manifestek
- `00-secrets.yaml`
  - Postgres user/jelszó secret
  - Django secret key secret
  - app config (`DATABASE_URL`, debug, hostok)
- `01-postgres.yaml`
  - Postgres PVC + Deployment + Service
- `02-media-pvc.yaml`
  - médiafájlok tartós tárolása (PVC)
- `03-build.yaml`
  - OpenShift ImageStream + BuildConfig (Git forrásból Docker build)
- `04-ksvc.yaml`
  - Knative Service a Django konténer futtatásához
  - media PVC csatolás

## 3.6 `photos/` – jelenleg nem használt scaffold app
- A `photos` mappa alap scaffold fájlokat tartalmaz, de nincs benne aktív üzleti logika.
- Az `INSTALLED_APPS` listában az `album` szerepel, nem a `photos`.

---

## 4. Domain modell részletesen

### `Photo` entitás
- `owner`: melyik user töltötte fel.
- `name`: felhasználói címke / megjelenített név.
- `image`: tényleges bináris médiafájl elérési útja.
- `uploaded_at`: létrehozási időbélyeg.

### Invariánsok és szabályok
- Egy kép mindig egy userhez tartozik (`CASCADE` törlés a userrel).
- A név hossza max 40 karakter.
- Új kép létrehozásakor az owner nem a formból jön, hanem a session userből.

---

## 5. AuthN/AuthZ logika

### AuthN (azonosítás)
- A Django beépített auth rendszerét használja (`django.contrib.auth`).
- Login/logout route-ok: `django.contrib.auth.urls`.
- Regisztráció: saját `signup` view `UserCreationForm`-mal.

### AuthZ (jogosultság)
- `@login_required`: feltöltés és törlés védett.
- Törlésnél explicit tulajdonosi ellenőrzés történik:
  - ha nem a tulajdonos: `403 Forbidden`.

---

## 6. Oldalak és user flow (végigvezetés)

1. **Nyitóoldal (`/`)**
   - Képlista jelenik meg.
   - Rendezés query paraméterrel váltható (`?sort=date` / `?sort=name`).

2. **Részletoldal (`/photos/<id>/`)**
   - Kép neve, feltöltési ideje, tulajdonosa és maga a kép jelenik meg.

3. **Regisztráció (`/signup/`)**
   - Sikeres regisztráció után automatikus belépés, redirect listára.

4. **Belépés (`/accounts/login/`)**
   - Django auth form.

5. **Feltöltés (`/upload/`)**
   - Multipart POST (`name`, `image`).
   - Siker után vissza a listára.

6. **Törlés (`/photos/<id>/delete/`)**
   - Először megerősítő oldal.
   - POST-ra fájl + DB rekord törlése.

---

## 7. Konfigurációs kulcsok (`.env` / környezeti változók)

Kiemelt változók:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`0` vagy `1`)
- `DJANGO_ALLOWED_HOSTS` (vesszővel elválasztva)
- `DJANGO_CSRF_TRUSTED_ORIGINS` (opcionális)
- `DATABASE_URL`
- `DJANGO_MEDIA_ROOT`
- `DJANGO_STATIC_ROOT`

Példa lokális `.env`:

```env
DJANGO_SECRET_KEY=dev-secret
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_MEDIA_ROOT=media
DJANGO_STATIC_ROOT=staticfiles
```

Postgres példa:

```env
DATABASE_URL=postgres://photoalbum:photoalbumpass@localhost:5432/photoalbum
```

---

## 8. Lokális futtatás – lépésről lépésre

### 8.1 Virtuális környezet és függőségek
```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

### 8.2 Migrációk
```bash
python manage.py makemigrations
python manage.py migrate
```

### 8.3 Admin user (opcionális)
```bash
python manage.py createsuperuser
```

### 8.4 Fejlesztői szerver
```bash
python manage.py runserver
```

---

## 9. Docker futtatási modell

### Build
```bash
docker build -t photoalbum:local .
```

### Run (példa)
```bash
docker run --rm -p 8080:8080 --env-file .env photoalbum:local
```

### Konténer induláskori parancs
A `Dockerfile` CMD szekvenciája:
1. `python manage.py migrate`
2. `python manage.py collectstatic --noinput`
3. `gunicorn config.wsgi:application --bind 0.0.0.0:8080 ...`

Ez azt jelenti, hogy minden konténerinduláskor automatikusan alkalmazza a migrációkat és összegyűjti a statikus fájlokat.

---

## 10. OpenShift/Kubernetes telepítési sorrend

Javasolt alkalmazási sorrend:

1. `k8s/00-secrets.yaml`
2. `k8s/01-postgres.yaml`
3. `k8s/02-media-pvc.yaml`
4. `k8s/03-build.yaml`
5. `k8s/04-ksvc.yaml`

### Mit csinál ez a lánc?
- Létrejönnek az app és DB titkok/configok.
- Elindul a Postgres tartós tárolóval.
- Létrejön külön PVC a médiafájlokhoz.
- OpenShift build pipeline GitHub repóból image-et épít.
- Knative Service futtatja az app image-et és mountolja a médiatárolót.

---

## 11. Biztonsági és üzemeltetési megjegyzések

- Production módban (`DJANGO_DEBUG=0`) secure cookie opciók aktiválódnak.
- A TLS termináció platformszinten (OpenShift Route) történik.
- A médiafájlokat itt Django szolgálja ki; nagy forgalomnál célszerű objektumtár (pl. S3-kompatibilis) használata.
- A `03-build.yaml` webhook secretjét és a Django secret key-t erősebb értékre kell cserélni éles környezetben.

---

## 12. Rövid fejlesztői térkép („mit hol keressek?”)

- Új mező a képhez → `album/models.py` + migration + template frissítés
- Új űrlapvalidáció → `album/forms.py`
- Új oldal/route → `album/urls.py` + `album/views.py` + template
- Jogosultsági logika → `album/views.py` (`login_required`, owner check)
- Auth oldalak testreszabása → `templates/registration/`
- K8s/OpenShift viselkedés → `k8s/*.yaml`
- Konténer startup/migrate/static → `Dockerfile`

---

## 13. Ismert jelenlegi állapotok

- A `photos/` app jelenleg scaffold maradvány, a tényleges implementáció az `album/` appban van.
- A repositoryban van `db.sqlite3`; a ténylegesen használt adatbázist mindig a `DATABASE_URL` dönti el.

---

## 14. Összefoglalás

A projekt egy letisztult, funkcionális Django fotóalbum alkalmazás, ahol az üzleti logika központja az `album` app.
Az architektúra egyszerű: URL → view → modell/form → template, kiegészítve auth védelemmel, fájlfeltöltéssel és OpenShift-kompatibilis konténeres futtatással.

Ha új funkciót fejlesztesz, érdemes mindig ebben a sorrendben gondolkodni:
1. URL és user flow
2. View + jogosultság
3. Modell/form/migration
4. Template
5. Deploy/runtime hatás (Docker/K8s)
