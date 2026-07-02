# Instrukcja — pobranie danych i automatyczna analiza

Cel: pobierasz **raz** dane wysokościowe dla swojego terenu, uruchamiasz jeden
skrypt, dostajesz gotowy `points.geojson` z wytypowanymi miejscami. Skrypt sam
liczy analizę archeologiczną (hillshade wielokierunkowy, Sky-View Factor,
spadki, Local Relief Model) i wskazuje anomalie geometryczne.

Twój teren: okolice **50°02′N 19°07′E** (dolina Pszczynki).

---

## KROK 1 — Pobierz dane NMT (bare-earth) z Geoportalu

To darmowe dane rządowe (GUGiK). Potrzebujesz **Numerycznego Modelu Terenu (NMT)**
— to grunt z usuniętą roślinnością, czyli dokładnie to, na czym widać obiekty
pod lasem.

1. Wejdź na **https://mapy.geoportal.gov.pl/imap/Imgp_2.html**
   (albo geoportal.gov.pl → „Mapa”).
2. Po prawej otwórz panel **„Dane do pobrania”**.
3. Zaznacz warstwę **„Numeryczny Model Terenu”** (NMT).
   - Najlepiej wybierz wariant **1 m** (siatka 1 m). Jeśli jest tylko 5 m —
     też zadziała, tylko z mniejszą precyzją.
4. W wyszukiwarce wpisz współrzędne swojego terenu:
   `50.0351, 19.1150` — mapa przeskoczy na miejsce.
5. Przybliż się. Na terenie pojawią się **prostokąty (arkusze)**. Kliknij ten,
   który pokrywa Twój obszar poszukiwań (a jeśli teren jest na styku — pobierz
   2–3 sąsiednie).
6. W okienku kliknij link pobierania. Dostaniesz plik **`.asc`**
   (Arc/Info ASCII GRID) — to jest to, czego potrzebuje skrypt.

> Alternatywa, jeśli powyższe okno jest niewygodne: na
> **https://geoportal.gov.pl** w sekcji „Dane do pobrania” działa ten sam
> mechanizm — klikasz arkusz nad swoim terenem i pobierasz NMT.

Zapisz plik np. jako `nmt.asc` w folderze z projektem.

---

## KROK 2 — Zainstaluj narzędzia (jednorazowo)

Potrzebujesz Pythona 3 (python.org). Potem w terminalu:

```bash
pip install whitebox rasterio numpy scipy pyproj
```

- **whitebox** — silnik analizy terenu (darmowy, używany w archeologii).
- **rasterio** — wczytywanie danych wysokościowych.
- **scipy / numpy** — wykrywanie anomalii.
- **pyproj** — przeliczenie współrzędnych na te, których używa mapa.

---

## KROK 3 — Uruchom analizę

W folderze z projektem:

```bash
python3 analiza_lidar.py --input nmt.asc
```

Skrypt:
1. wczyta NMT,
2. policzy wizualizacje (zapisze je w folderze `_analiza/` — możesz je obejrzeć
   w QGIS jako obrazy terenu),
3. wykryje geometryczne anomalie (regularne nasypy i zagłębienia),
4. nadpisze **`points.geojson`** wytypowanymi punktami z opisem każdego.

Wynik na ekranie powie, ile punktów znalazł i gdzie leżą pliki.

---

## KROK 4 — Zobacz wynik na mapie

1. Podmień `points.geojson` w swoim repozytorium GitHub na nowo wygenerowany.
2. Odśwież stronę (dodaj `?v=4` na końcu adresu, żeby ominąć cache).
3. Punkty pojawią się na mapie:
   - **pomarańczowe (wysoki priorytet)** — najsilniejsze, najbardziej regularne
     anomalie: zacznij od nich,
   - **zielone (do sprawdzenia)** — słabsze sygnały.
   Każdy punkt po kliknięciu pokazuje, dlaczego został wskazany (amplituda,
   powierzchnia, zwartość kształtu, typ: nasyp czy zagłębienie).

---

## Jak to czytać — i czego NIE zakładać

- Skrypt wskazuje **geometryczne anomalie terenu** — miejsca, które „nie
  wyglądają naturalnie”. To hipotezy, nie potwierdzone bunkry. Weryfikacja =
  teren.
- Anomalią bywa też: piwnica, fundament, hałda, lej, okop, stara droga. Kontekst
  rozstrzyga.
- Regulowanie czułości: w `analiza_lidar.py` w funkcji `wykryj_anomalie`
  możesz zmienić `min_area_m2` / `max_area_m2` (zakres wielkości obiektu) oraz
  próg `2.5 * std` (niżej = więcej punktów, ale więcej fałszywych).

## Weryfikacja w terenie — ostrożnie

Wejścia do nieznanych obiektów podziemnych bywają groźne (zawały, brak tlenu,
niewybuchy) — nie wchodź sam. W Polsce poszukiwania zabytków często wymagają
zgody wojewódzkiego konserwatora zabytków; sprawdź status terenu, zanim ruszysz.

*Źródło danych: Główny Urząd Geodezji i Kartografii (Geoportal), NMT z LiDAR —
darmowe do dowolnego użytku.*
