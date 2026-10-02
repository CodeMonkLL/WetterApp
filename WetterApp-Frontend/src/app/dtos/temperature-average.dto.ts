/**
 * Antwort von GET /api/measurements/temperature-average.
 *
 * Die Mittelwerte gelten für den kompletten gefilterten Zeitraum, nicht nur
 * für die gerade angezeigte Tabellenseite. Ohne Treffer sind sie null.
 */
export interface TemperatureAverageDto {
  station_id: string | null;
  /** Gesuchter Zeitraum, null wenn nicht gefiltert wurde. */
  date_from: string | null;
  date_to: string | null;
  /** Zeitraum, für den tatsächlich Messwerte vorliegen. */
  data_from: string | null;
  data_to: string | null;
  /** Anzahl Tage mit vorhandenem Tagesmittel. */
  days: number;

  /** Mittel der Tagesmittel (°C). */
  avg_tmk: number | null;
  /** Mittel der Tagesmaxima (°C). */
  avg_txk: number | null;
  /** Mittel der Tagesminima (°C). */
  avg_tnk: number | null;
}
