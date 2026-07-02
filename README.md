# Analiza terenu LiDAR — rozpoznanie obiektów podziemnych

Interaktywna mapa nakładająca **cieniowany relief i hipsometrię z lotniczego
skaningu laserowego (LiDAR/ALS)** — dane z polskiego Geoportalu GUGiK — na
ortofotomapę. Służy do wyszukiwania geometrycznych anomalii terenu (potencjalne
bunkry, schrony, wejścia, drogi dojazdowe) pod pokrywą leśną.

> **Ważne, uczciwie:** ta mapa *pokazuje* dane LiDAR, ale nie typuje punktów za
> Ciebie. Punkty w `points.geojson` to na razie **przykłady**. Właściwa analiza
> polega na tym, że **Ty oglądasz relief i zaznaczasz anomalie** według zasad
> opisanych w panelu mapy i niżej. To standardowe podejście w archeologii:
> anomalia = hipoteza do sprawdzenia w terenie, nie dowód.

---

## 1. Pliki

| Plik | Co robi |
|---|---|
| `index.html` | Mapa. Warstwy LiDAR + panel z metodyką. Otwórz w przeglądarce. |
| `config.js` | Środek i przybliżenie startowe mapy. **Podmień współrzędne.** |
| `points.geojson` | Twoje punkty i obszar. **To tu pracujesz.** |
| `README.md` | Ten plik. |

---

## 2. Uruchomienie na GitHub (GitHub Pages)

1. Załóż repozytorium na GitHub (np. `bunkry-lidar`).
2. Wgraj wszystkie 4 pliki do głównego katalogu repo.
3. **Settings → Pages → Branch: `main` / folder `/root` → Save.**
4. Po chwili mapa będzie pod `https://TWOJ-LOGIN.github.io/bunkry-lidar/`.

Nie musisz nic budować — to statyczne pliki.

> Test lokalny: dwuklik `index.html` zwykluje ostrzeżenie CORS przy
> `points.geojson`. Uruchom mini-serwer w folderze:
> `python3 -m http.server` → wejdź na `http://localhost:8000`.

---

## 3. Ustaw lokalizację

W `config.js` podmień `center` na dokładne współrzędne swojego terenu:

- Google Maps → **klik prawym** na miejsce → pierwsza pozycja w menu to
  `szerokość, długość` (lat, lng). Kliknij, by skopiować.
- Wklej jako `center: [lat, lng]`.

Jeśli `points.geojson` ma punkty, mapa i tak sama dopasuje widok do nich.

---

## 4. Edycja punktów — sedno pracy

Otwórz `points.geojson`. Każdy obiekt to jeden „Feature". Kopiuj i wklejaj
bloki. **Uwaga na kolejność współrzędnych** — GeoJSON używa
`[długość, szerokość]` czyli `[lng, lat]` (odwrotnie niż Google Maps!).

Wzór punktu:

```json
{
  "type": "Feature",
  "properties": {
    "type": "high",
    "name": "Anomalia A",
    "why": "Prostokątny nasyp ~10×6 m, kąty proste, niewidoczny na ortofoto, ostry na reliefie.",
    "confidence": "do weryfikacji"
  },
  "geometry": { "type": "Point", "coordinates": [21.8520, 50.6615] }
}
```

`type` przyjmuje:

- `confirmed` — czerwony — obiekt potwierdzony (Twój znaleziony fragment)
- `high` — bursztynowy — silna geometryczna anomalia
- `check` — zielony — słabszy / niejednoznaczny sygnał
- `context` — niebieski — droga, wał, oś układu (Point lub LineString)
- `area` — czerwony obrys — obszar zainteresowania (Polygon)

---

## 5. Jak czytać relief — na co polować

Natura nie robi kątów prostych. Obiekty inżynieryjne — tak. Szukaj:

- **prostokątów i linii prostych** — stropy, ściany, nasypy;
- **regularnych zagłębień** — zapadnięte stropy, szyby, wejścia (ostro
  obrysowane doły);
- **kopców o zbyt równych bokach** — nasypy maskujące nad komorami;
- **prostych wcięć/nasypów urywających się w lesie** — drogi dojazdowe do wejść;
- **wałów i fos** — obwałowania wokół obiektu;
- **powtarzalności** — obiekty wojskowe budowano seryjnie; jeden wzór w rzędzie
  to mocny trop.

Najlepsi kandydaci: **niewidoczne na ortofoto, wyraźne na reliefie.**
Przełączaj warstwy i zmieniaj krycie suwakami, by je wyłapać.

---

## 6. Chcesz precyzyjniejszej analizy? Pobierz surowe dane LiDAR

Mapa pokazuje gotowe cieniowanie WMS. Dla własnych, mocniejszych wizualizacji
(hillshade z wielu kierunków, Sky-View Factor, mapa spadków, Local Relief Model)
pobierz surowe dane i przetwórz w QGIS:

- **Chmura punktów LAZ** oraz **NMT (bare-earth)** — darmowo z
  `geoportal.gov.pl` → „Dane do pobrania" → *Numeryczny Model Terenu* /
  *Dane pomiarowe LIDAR*. Kliknij arkusz nad swoim terenem, pobierz.
- W **QGIS**: wczytaj NMT → *Raster ▸ Analiza terenu ▸ Cieniowanie/ Spadek*.
  Zmieniaj azymut światła (315°, 45°, 135°…) — obiekty równoległe do promieni
  giną przy jednym kierunku, wychodzą przy innym.
- Wtyczka **Relief Visualization Toolbox (RVT)** daje Sky-View Factor i
  Openness — najlepsze do subtelnych, płaskich obiektów pod lasem.

Gdy zidentyfikujesz obiekt, odczytaj jego współrzędne w QGIS i dopisz punkt do
`points.geojson`.

---

## 7. Zdrowy rozsądek i prawo

- Anomalia terenu ≠ potwierdzony bunkier. Weryfikacja wymaga terenu.
- Wejścia do nieznanych obiektów podziemnych bywają **niebezpieczne**
  (zawały, brak tlenu, niewybuchy). Nie wchodź sam i bez zabezpieczenia.
- Sprawdź status terenu i przepisy o poszukiwaniach zabytków w Polsce —
  na wielu obszarach eksploracja wymaga zgody konserwatora zabytków.

*Źródło danych wysokościowych: Główny Urząd Geodezji i Kartografii (Geoportal),
usługi WMS. Podkład ortofoto: Esri World Imagery.*
