// ── Konfiguracja mapy ────────────────────────────────────────────────
// Ustaw środek na swój teren. [szerokość, długość] w stopniach (WGS84).
// Jak zdobyć dokładne współrzędne:
//   Google Maps → klik prawym na punkt → pierwsza pozycja to lat, lng.
//   Skopiuj i wklej poniżej. Obecne wartości są PRZYBLIŻONE (Kolonia Wola)
//   i służą tylko jako punkt startowy — popraw je.
//
// Uwaga: gdy points.geojson ma punkty, mapa i tak dopasuje widok do nich
// automatycznie. Center/zoom to pozycja awaryjna.

window.APP_CONFIG = {
center: [50.66, 21.85],   // ← PODMIEŃ na dokładne lat, lng swojego terenu
zoom:   15
};
