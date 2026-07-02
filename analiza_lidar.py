#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 ANALIZA TERENU LiDAR — automatyczna detekcja obiektow (bunkry / schrony)
 Metodyka: standardowy warsztat archeologiczny na danych ALS
   hillshade wielokierunkowy + Sky-View Factor + spadki + Local Relief Model
   -> wykrycie geometrycznych anomalii -> eksport do points.geojson
============================================================================

CO ROBI TEN SKRYPT (w skrocie):
  1. Wczytuje Twoj plik NMT (bare-earth) pobrany z Geoportalu.
  2. Liczy zestaw wizualizacji uzywanych w archeologii do wykrywania
     obiektow pod pokrywa lesna.
  3. Automatycznie znajduje miejsca o "nienaturalnej" geometrii
     (regularne zaglebienia, ostre krawedzie, lokalne wypietrzenia).
  4. Zapisuje je jako punkty do points.geojson — te same, ktore
     wyswietla Twoja mapa index.html.

URUCHOMIENIE:
  python3 analiza_lidar.py --input SCIEZKA/DO/nmt.asc

Wymagania (jednorazowa instalacja):
  pip install whitebox rasterio numpy scipy

Pelna instrukcja pobierania danych: patrz INSTRUKCJA_DANE.md
============================================================================
"""

import argparse, json, os, sys, math

def need(pkg):
    try:
        __import__(pkg)
    except ImportError:
        sys.exit(f"[BLAD] Brakuje biblioteki '{pkg}'. Zainstaluj:\n"
                 f"       pip install whitebox rasterio numpy scipy")

for p in ("numpy","rasterio","scipy","whitebox"):
    need(p)

import numpy as np
import rasterio
from rasterio.transform import xy
from scipy import ndimage
import whitebox

wbt = whitebox.WhiteboxTools()
wbt.verbose = False


# ─────────────────────────────────────────────────────────────────────────
def przygotuj_dtm(input_path, work):
    """Wczytuje NMT, zamienia braki (-9999) na NaN, zwraca sciezke GeoTIFF."""
    print("[1/5] Wczytuje NMT:", input_path)
    with rasterio.open(input_path) as src:
        dem = src.read(1).astype("float32")
        prof = src.profile
        crs = src.crs
        transform = src.transform
        res = src.res[0]
    dem[dem <= -9990] = np.nan
    prof.update(dtype="float32", nodata=np.nan, count=1, driver="GTiff")
    dtm_tif = os.path.join(work, "dtm.tif")
    with rasterio.open(dtm_tif, "w", **prof) as dst:
        dst.write(dem, 1)
    print(f"      rozmiar: {dem.shape[1]}x{dem.shape[0]} px, rozdzielczosc ~{res:.2f} m")
    if crs is None:
        print("      [UWAGA] plik nie ma ukladu wspolrzednych (CRS). "
              "Jesli punkty wyjda w zlym miejscu, ustaw EPSG:2180 w QGIS.")
    return dtm_tif, dem, transform, crs, res


# ─────────────────────────────────────────────────────────────────────────
def wizualizacje(dtm_tif, work):
    """Liczy wizualizacje archeologiczne przez WhiteboxTools."""
    print("[2/5] Licze wizualizacje (hillshade / SVF / spadki / LRM)...")

    # a) hillshade wielokierunkowy — laczy oswietlenie z wielu azymutow,
    #    dzieki czemu nie gubi obiektow rownoleglych do jednego kierunku swiatla
    multi = os.path.join(work, "hillshade_multi.tif")
    wbt.multidirectional_hillshade(dtm_tif, multi)

    # b) Sky-View Factor — najlepszy do plaskich, subtelnych obiektow pod lasem;
    #    zaglebienia (wejscia, zapadniete stropy) maja niski SVF
    svf = os.path.join(work, "svf.tif")
    try:
        wbt.sky_view_factor(dtm_tif, svf)
    except Exception:
        # starsze wersje: nazwa parametru inna — fallback na openness
        wbt.openness(dtm_tif, svf, os.path.join(work,"_neg.tif"), dist=25)

    # c) spadki — uwypuklaja skarpy, sciany, krawedzie nasypow
    slope = os.path.join(work, "slope.tif")
    wbt.slope(dtm_tif, slope, units="degrees")

    # d) Local Relief Model — usuwa duza forme terenu, zostawia
    #    lokalne odchylki (kopce, doly, nasypy) — serce detekcji
    #    LRM = DTM - DTM_wygladzony
    smooth = os.path.join(work, "dtm_smooth.tif")
    wbt.mean_filter(dtm_tif, smooth, filterx=25, filtery=25)
    lrm = os.path.join(work, "lrm.tif")
    wbt.subtract(dtm_tif, smooth, lrm)

    print("      gotowe: hillshade_multi, svf, slope, lrm")
    return {"multi": multi, "svf": svf, "slope": slope, "lrm": lrm}


# ─────────────────────────────────────────────────────────────────────────
def wykryj_anomalie(vis, transform, crs, res, work,
                    min_area_m2=6.0, max_area_m2=600.0):
    """
    Szuka geometrycznych anomalii na Local Relief Model.
    Obiekty typu bunkier: lokalne wypietrzenie (strop/nasyp) LUB
    ostre zaglebienie (wejscie/zapadniety strop) o zwartym, regularnym ksztalcie.
    """
    print("[3/5] Wykrywam anomalie na LRM...")
    with rasterio.open(vis["lrm"]) as src:
        lrm = src.read(1).astype("float32")
    lrm = np.nan_to_num(lrm, nan=0.0)

    # prog: odchylenia silniejsze niz 2.5 * odchylenie standardowe lokalnego reliefu
    std = np.nanstd(lrm)
    prog = 2.5 * std
    print(f"      odchylenie std LRM = {std:.2f} m, prog wykrycia = ±{prog:.2f} m")

    wypietrzenia = lrm > prog     # nasypy, stropy, kopce
    zaglebienia = lrm < -prog     # wejscia, zapadniete stropy, rowy

    px_area = res * res
    min_px = max(3, int(min_area_m2 / px_area))
    max_px = int(max_area_m2 / px_area)

    kandydaci = []
    for maska, kind in ((wypietrzenia, "wypietrzenie"), (zaglebienia, "zaglebienie")):
        lab, n = ndimage.label(maska)
        for i in range(1, n + 1):
            ys, xs = np.where(lab == i)
            area = len(xs)
            if area < min_px or area > max_px:
                continue
            # zwartosc ksztaltu — obiekty inzynieryjne sa regularne, nie postrzepione
            h = ys.max() - ys.min() + 1
            w = xs.max() - xs.min() + 1
            wypelnienie = area / (h * w)          # 1.0 = idealny prostokat/owal
            wydluzenie = max(h, w) / max(1, min(h, w))
            if wypelnienie < 0.45:                # odrzuc rozlazle, naturalne formy
                continue
            cy, cx = ys.mean(), xs.mean()
            amp = float(np.mean(np.abs(lrm[ys, xs])))
            # scoring: silne odchylenie + zwartosc = wysoki priorytet
            score = amp * wypelnienie
            kandydaci.append({
                "row": cy, "col": cx, "area_m2": area * px_area,
                "amp": amp, "fill": wypelnienie, "elong": wydluzenie,
                "kind": kind, "score": score
            })

    kandydaci.sort(key=lambda d: d["score"], reverse=True)
    print(f"      znaleziono {len(kandydaci)} kandydatow (przed filtrem koncowym)")
    return kandydaci[:40]   # max 40 najsilniejszych


# ─────────────────────────────────────────────────────────────────────────
def do_geojson(kandydaci, transform, crs, res, out_path):
    """Zamienia kandydatow na points.geojson zgodny z Twoja mapa."""
    print("[4/5] Zapisuje points.geojson...")

    # transformacja piksel -> wspolrzedne mapy; jesli CRS to 2180, przelicz do WGS84
    to_wgs = None
    if crs is not None:
        try:
            from pyproj import Transformer
            to_wgs = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        except Exception:
            to_wgs = None

    feats = []
    for rank, k in enumerate(kandydaci, 1):
        X, Y = xy(transform, k["row"], k["col"])   # w ukladzie zrodlowym
        if to_wgs:
            lng, lat = to_wgs.transform(X, Y)
        else:
            lng, lat = X, Y   # zakładamy, ze juz WGS84 (rzadko)

        # klasyfikacja priorytetu
        if rank <= 5:
            typ, ety = "high", "Wysoki priorytet"
        elif rank <= 15:
            typ, ety = "check", "Do sprawdzenia"
        else:
            typ, ety = "check", "Slaby sygnal"

        opis = (f"Anomalia #{rank} ({k['kind']}). "
                f"Amplituda ~{k['amp']:.2f} m, powierzchnia ~{k['area_m2']:.0f} m², "
                f"zwartosc ksztaltu {k['fill']:.2f} (1.0=regularny). "
                f"{'Lokalne wypietrzenie — mozliwy strop/nasyp nad komora.' if k['kind']=='wypietrzenie' else 'Ostre zaglebienie — mozliwe wejscie lub zapadniety strop.'}")

        feats.append({
            "type": "Feature",
            "properties": {
                "type": typ, "name": f"Anomalia #{rank}",
                "why": opis,
                "confidence": f"score {k['score']:.2f} — do weryfikacji w terenie"
            },
            "geometry": {"type": "Point",
                         "coordinates": [round(lng, 6), round(lat, 6)]}
        })

    fc = {"type": "FeatureCollection",
          "note": "Wygenerowane automatycznie przez analiza_lidar.py z danych NMT/LiDAR. "
                  "Kazdy punkt to geometryczna anomalia terenu — hipoteza do weryfikacji.",
          "features": feats}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    print(f"      zapisano {len(feats)} punktow -> {out_path}")


# ─────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Analiza terenu LiDAR -> points.geojson")
    ap.add_argument("--input", required=True, help="plik NMT (.asc / .tif) z Geoportalu")
    ap.add_argument("--out", default="points.geojson", help="wyjsciowy geojson")
    ap.add_argument("--work", default="_analiza", help="folder na pliki posrednie")
    args = ap.parse_args()

    os.makedirs(args.work, exist_ok=True)
    wbt.work_dir = os.path.abspath(args.work)

    dtm_tif, dem, transform, crs, res = przygotuj_dtm(args.input, args.work)
    vis = wizualizacje(dtm_tif, args.work)
    kand = wykryj_anomalie(vis, transform, crs, res, args.work)
    do_geojson(kand, transform, crs, res, args.out)

    print("[5/5] GOTOWE.")
    print("      Wizualizacje (otworz w QGIS, by obejrzec teren):")
    for k, v in vis.items():
        print(f"        - {v}")
    print(f"      Punkty wgraj do repo (podmien {args.out}) i odswiez mape.")


if __name__ == "__main__":
    main()
