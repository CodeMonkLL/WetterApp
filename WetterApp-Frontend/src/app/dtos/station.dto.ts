/** Stammdaten einer DWD-Wetterstation. Datumsfelder sind ISO-Strings (YYYY-MM-DD). */
export interface StationDto {
  station_id: string;
  name: string;
  state: string | null;
  height: number | null;
  latitude: number | null;
  longitude: number | null;
  /** Beginn des Messzeitraums laut DWD-Stationsliste. */
  active_from: string | null;
  /** Ende des Messzeitraums laut DWD-Stationsliste. */
  active_to: string | null;
}
