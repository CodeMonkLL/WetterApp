import { DailyMeasurementDto } from './daily-measurement.dto';
import { StationDto } from './station.dto';

/**
 * Stammdaten einer Station samt tatsächlich vorhandenem Datenbestand.
 *
 * `station.active_from`/`active_to` stammen aus der DWD-Stationsliste,
 * `data_from`/`data_to` sagen, was davon wirklich importiert wurde.
 * Ohne importierte Messwerte sind beide null.
 */
export interface StationOverviewDto {
  station: StationDto;
  data_from: string | null;
  data_to: string | null;
  latest: DailyMeasurementDto | null;
}
