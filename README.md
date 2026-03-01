Photoalbum – végleges megoldás dokumentáció
Projekt áttekintés

A feladat célja egy skálázható fényképalbum‑alkalmazás létrehozása egy publikus PaaS környezetben.
A projekt Python + Django keretrendszerre épül, és az alkalmazás konténerben fut az OpenShift Developer Sandbox klaszteren.
A felhasználók fényképeket tölthetnek fel, listázhatják azokat név vagy dátum szerint, valamint megtekinthetik a részleteket.
A rendszer felhasználókezelést (regisztráció, belépés, kilépés) és jogosultság‑ellenőrzést biztosít.

Környezet
Komponens	Leírás
PaaS	Red Hat OKD 4 (OpenShift Developer Sandbox)
Programnyelv/keretrendszer	Python 3 + Django
Tárolótechnológia	Dockerfile alapú build, OpenShift BuildConfig használatával
CI/CD	GitHub webhookok által indított OpenShift BuildConfig builds
Adatbázis	Neon Postgres (felhőalapú, külső adatbázis‑szolgáltatás)
Persistent storage	CephFS alapú PVC (ReadWriteMany), a képek és médiatartalom tárolására
Deployment stratégiája	RollingUpdate, amely lehetővé teszi a zéró állásidőt
Architektúra és rétegek
Alkalmazási réteg

A Django webalkalmazás egy konténerben fut; a Deployment erőforrás gondoskodik a példányok számáról és a RollingUpdate frissítési stratégiáról.

A statikus fájlokat (CSS/JS) a WhiteNoise middleware szolgálja ki. A collectstatic parancs a statikus tartalmat egy emptyDir kötetbe gyűjti össze a build során.

Az alkalmazás MEDIA_ROOT könyvtára persistent volume claimre van mountolva, így a felhasználók által feltöltött képek a podok újraindítása után is megmaradnak.

A konfigurációs értékeket (adatbázis URI, titkos kulcs, engedélyezett hosztok) környezeti változókkal adjuk át a konténernek.

Adatbázis‑réteg

A Neon Postgres egy teljesen menedzselt, külső adatbázis‑szolgáltatás. Az alkalmazás a DATABASE_URL környezeti változón keresztül kapcsolódik hozzá.

Mivel az adatbázis a klaszteren kívül helyezkedik el, külön adatbázis‑rétegként funkcionál, megfelelve a többrétegű elvnek.

Tároló réteg

A feltöltött médiatartalom (képek) tárolására persistent volume claimet használunk. Az első verzióban ReadWriteOnce access mód volt beállítva, ami csupán egy pod/node számára tette elérhetővé a kötetet.

A skálázhatóság érdekében a végleges megoldás ReadWriteMany módú CephFS storage classot használ (media-pvc-rwx), amely lehetővé teszi, hogy több pod írjon és olvasson ugyanabból a kötetből egyszerre.

A PVC a podban a /data/media útvonalra van mountolva, ezt a DJANGO_MEDIA_ROOT környezeti változó adja át a Django beállításainak.

Alternatív megoldásként S3/MinIO típusú objekt‑tároló is használható, ami még jobb horizontális skálázhatóságot biztosít.

CI/CD réteg

Az OpenShift BuildConfig és ImageStream erőforrásai gondoskodnak a container image építéséről. A BuildConfig a GitHub repository main branchéről építi az image‑t.

A triggers szakaszban GitHub webhook van beállítva; minden push esemény új buildet generál. Az automatikus buildhez létre kell hozni egy megfelelő titkos kulcsot, és a webhook URL‑t be kell állítani a GitHub repóban.

Sikeres build után az ImageStream új :latest taget kap, ami ImageChange triggerrel frissíti a Deployment podsorozatát.

Hálózati réteg

A belső szolgáltatások (Deployment → Service) között OpenShift belső DNS nevek alapján történik a kommunikáció.

A külvilág számára az Route erőforrás biztosít HTTPS végpontot, amely a felhasználói kéréseket a futó podokra irányítja.

A USE_X_FORWARDED_HOST és a SECURE_PROXY_SSL_HEADER beállítások a Django alkalmazásban engedélyezik a Reverse Proxy mögötti biztonságos működést.

Telepítési lépések összefoglalója

Fejlesztői környezet: helyben Python + Django virtualenv, SQLite adatbázissal. Az alkalmazás funkcionalitását itt lehet fejleszteni és tesztelni.

Konténerizálás: a projekt gyökérkönyvtárában lévő Dockerfile készíti el a futtatókörnyezetet. A requirements.txt telepíti a függőségeket, a collectstatic és a migrációk a build részeként futnak.

Git: a forráskód felkerül a GitHub‑ra; a repository‑hoz hozzáadott BuildConfig‑webhook gondoskodik róla, hogy push után automatikusan build induljon.

OpenShift erőforrások:

03-build.yaml – ImageStream és BuildConfig definíció, GitHub webhook triggellel.

Deployment – a konténer futtatása, a környezeti változók és a volume mountok megadása.

Service és Route – belső és külső elérhetőség biztosítása.

PersistentVolumeClaim – media-pvc-rwx, ReadWriteMany access móddal.

CI/CD pipeline tesztelése: egy commit/push a repóban új buildet indít; a BuildConfig logjaiban követhető a build státusza. Sikeres build után a Deployment frissül.

Skálázás: a Deployment replikaszámának növelésével több pod futhat. A media-pvc-rwx RWX módú kötet minden pod számára elérhető, így a feltöltött képek mindegyik példányból láthatók.

Kapcsolatok és biztonsági beállítások

Adatbázis‑kapcsolat: a DATABASE_URL környezeti változó a Neon Postgres URI‑t tartalmazza.

Media storage: a PVC a media-storage nevű volume‑on keresztül csatlakozik; a DJANGO_MEDIA_ROOT és MEDIA_URL beállítások biztosítják, hogy a képek a /media/… útvonalon jelenjenek meg.

Webhook jogosultság: OKD 4‑ben a GitHub webhookok csak akkor érik el a BuildConfigot, ha a system:unauthenticated csoport rendelkezik a system:webhook jogosultsággal. Ezt egy RoleBinding létrehozásával állítottuk be.

Titok kezelése: a GitHub és a BuildConfig ugyanazt a titkos kulcsot használja; javasolt erős, véletlenszerű kulcs használata.

Biztonságos HTTP: a Route TLS terminációt végez; a Django oldalán a SECURE_PROXY_SSL_HEADER van beállítva, így nem történik ismételt SSL redirect.

Neon mint külön adatbázis

A Neon Postgres szolgáltatás a klaszteren kívül fut, független hoszton. Az alkalmazás csak TCP kapcsolaton keresztül éri el a Neon DB‑t, így az adatbázis réteg fizikailag és logikailag elkülönül az alkalmazásrétegtől. Ez a szétválasztás megfelel a többrétegű architektúra követelményeinek.

Jövőbeli fejlesztési lehetőségek

Objekt‑tároló bevezetése: hosszú távon célszerű S3‑kompatibilis tárhelyet használni a médiafájlokhoz, mivel az jobban kezeli a konkurens írásokat és rugalmasságot ad a replikák számának növeléséhez.

Horizontális autoscaling: HPA (Horizontal Pod Autoscaler) beállítása CPU/ memória terhelés alapján, ami dinamikusan növeli vagy csökkenti a podok számát.

CI/CD bővítése: integráció minőségbiztosítási lépésekkel (tesztek, linter), vagy staging környezet a release előtti ellenőrzésekhez.

Ez a dokumentáció összefoglalja a végleges fényképalbum‑alkalmazás architektúráját és a környezet főbb beállításait. A cél egy skálázható, több rétegű, felhőalapú megoldás volt, amely elválasztja az alkalmazást, az adatbázist és a tárolót, és automatikus build‑ és deployment‑folyamattal működik.