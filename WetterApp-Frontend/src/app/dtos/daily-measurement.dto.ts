/**
 * Ein Tageswert einer Station. `date` ist ein ISO-String (YYYY-MM-DD).
 * Fehlende Messwerte liefert das Backend als null (im DWD-Rohdatensatz -999).
 */
export interface DailyMeasurementDto {
  station_id: string;
  date: string;

  /** Qualitätsniveau der Winddaten. */
  qn3: number | null;
  /** Qualitätsniveau der übrigen Daten. */
  qn4: number | null;

  /** Windspitze (m/s). */
  fx: number | null;
  /** Tagesmittel Wind (m/s). */
  fm: number | null;

  /** Niederschlagshöhe (mm). */
  rsk: number | null;
  /** Niederschlagsform. */
  rskf: number | null;
  /** Schneehöhe (cm). */
  shk_tag: number | null;

  /** Sonnenscheindauer (h). */
  sdk: number | null;
  /** Bedeckungsgrad (1/8). */
  nm: number | null;

  /** Dampfdruck (hPa). */
  vpm: number | null;
  /** Luftdruck (hPa). */
  pm: number | null;
  /** Relative Feuchte (%). */
  upm: number | null;

  /** Tagesmittel Temperatur (°C). */
  tmk: number | null;
  /** Tagesmaximum (°C). */
  txk: number | null;
  /** Tagesminimum (°C). */
  tnk: number | null;
  /** Minimum 5 cm über Boden (°C). */
  tgk: number | null;
}
