/** Zeitliche Auflösung der Ortsauswertung. */
export type AnalysisResolution = 'day' | 'month' | 'year';

/** In die Auswertung eingeflossene Nachbarstation. */
export interface NeighborStationDto {
  station_id: string;
  name: string;
  state: string | null;
  height: number | null;
  latitude: number;
  longitude: number;
  distance_km: number;
  /** Anteil am Mittel (0-1), wenn an dem Tag alle Stationen einen Wert liefern. */
  weight: number;
}

/**
 * Interpolierte Werte für einen Tag, Monat oder ein Jahr.
 *
 * `days` zählt die Tage mit Messwert, Summen beziehen sich nur auf diese Tage.
 */
export interface AnalysisPeriodDto {
  /** "YYYY-MM-DD", "YYYY-MM" oder "YYYY". */
  period: string;
  days: number;
  /** Mittel der Tagesmittel (°C). */
  tmk: number | null;
  /** Mittel der Tagesmaxima (°C). */
  txk: number | null;
  /** Mittel der Tagesminima (°C). */
  tnk: number | null;
  /** Mittlere Windgeschwindigkeit (m/s). */
  fm: number | null;
  /** Mittlere relative Feuchte (%). */
  upm: number | null;
  /** Niederschlagssumme (mm). */
  rsk: number | null;
  /** Sonnenscheinsumme (h). */
  sdk: number | null;
}

/** Antwort von GET /api/analysis/location. */
export interface LocationAnalysisDto {
  address: string | null;
  /** Vom Geocoder aufgelöste Adresse, bei Eingabe per Koordinaten der nächste Ort. */
  display_name: string | null;
  latitude: number;
  longitude: number;
  /** Höhe des Ortes, auf die Temperaturen umgerechnet wurden. */
  target_height: number | null;
  date_from: string;
  date_to: string;
  resolution: AnalysisResolution;
  stations: NeighborStationDto[];
  series: AnalysisPeriodDto[];
}

/** Antwort von GET /api/stations/{stationId}/analysis. */
export interface StationAnalysisDto {
  station_id: string;
  /** Ausgewerteter Zeitraum, null wenn die Station keine Messwerte hat. */
  date_from: string | null;
  date_to: string | null;
  resolution: AnalysisResolution;
  series: AnalysisPeriodDto[];
}
