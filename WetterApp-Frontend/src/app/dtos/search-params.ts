/** Query-Parameter für GET /api/stations. */
export interface StationSearchParams {
  /** Teil des Stationsnamens, Groß-/Kleinschreibung egal. */
  name?: string;
  /** Bundesland, exakter Treffer. */
  state?: string;
  /** Nur Stationen, die ab diesem Datum noch Werte liefern (YYYY-MM-DD). */
  dateFrom?: string;
  /** Nur Stationen, die bis zu diesem Datum schon Werte liefern (YYYY-MM-DD). */
  dateTo?: string;
  limit?: number;
  offset?: number;
}

/** Query-Parameter für GET /api/measurements. */
export interface MeasurementSearchParams {
  /** Exakte DWD-Station-ID, z.B. "00555". */
  stationId?: string;
  /** Teil des Stationsnamens. Kann mehrere Stationen mischen. */
  stationName?: string;
  state?: string;
  /** Frühestes Messdatum, einschließlich (YYYY-MM-DD). */
  dateFrom?: string;
  /** Spätestes Messdatum, einschließlich (YYYY-MM-DD). */
  dateTo?: string;
  order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

/** Query-Parameter für GET /api/measurements/temperature-average. */
export type TemperatureAverageParams = Omit<
  MeasurementSearchParams,
  'order' | 'limit' | 'offset'
>;
