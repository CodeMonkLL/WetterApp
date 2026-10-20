import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AnalysisResolution,
  DailyMeasurementDto,
  LocationAnalysisDto,
  LocationAnalysisParams,
  MeasurementSearchParams,
  PagedResult,
  StationAnalysisDto,
  StationDto,
  StationOverviewDto,
  StationSearchParams,
  TemperatureAverageDto,
  TemperatureAverageParams,
} from '../dtos';

/** Bindet alle Routen des Flask-Backends ein. */
@Injectable({ providedIn: 'root' })
export class WeatherApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api';

  /** GET /api/health */
  checkHealth(): Observable<{ status: string; message: string }> {
    return this.http.get<{ status: string; message: string }>(
      `${this.baseUrl}/health`,
    );
  }

  /**
   * GET /api/stations
   *
   * Die Datumsgrenzen filtern über Überlappung: gefunden wird jede Station,
   * deren Messzeitraum den gesuchten Zeitraum schneidet.
   */
  searchStations(
    params: StationSearchParams = {},
  ): Observable<PagedResult<StationDto>> {
    const httpParams = buildParams({
      name: params.name,
      date_from: params.dateFrom,
      date_to: params.dateTo,
      limit: params.limit,
      offset: params.offset,
    });
    return this.http.get<PagedResult<StationDto>>(`${this.baseUrl}/stations`, {
      params: httpParams,
    });
  }

  /** GET /api/stations/{stationId} */
  getStation(stationId: string): Observable<StationDto> {
    return this.http.get<StationDto>(
      `${this.baseUrl}/stations/${encodeURIComponent(stationId)}`,
    );
  }

  /**
   * GET /api/stations/{stationId}/overview
   *
   * Liefert den tatsächlich importierten Datenbestand, eignet sich also zum
   * Begrenzen einer Datumsauswahl.
   */
  getStationOverview(stationId: string): Observable<StationOverviewDto> {
    return this.http.get<StationOverviewDto>(
      `${this.baseUrl}/stations/${encodeURIComponent(stationId)}/overview`,
    );
  }

  /**
   * GET /api/stations/{stationId}/analysis
   *
   * Ohne Datumsgrenzen wertet das Backend den gesamten importierten Bestand aus.
   */
  getStationAnalysis(
    stationId: string,
    params: {
      dateFrom?: string;
      dateTo?: string;
      resolution?: AnalysisResolution;
    },
  ): Observable<StationAnalysisDto> {
    const httpParams = buildParams({
      date_from: params.dateFrom,
      date_to: params.dateTo,
      resolution: params.resolution,
    });
    return this.http.get<StationAnalysisDto>(
      `${this.baseUrl}/stations/${encodeURIComponent(stationId)}/analysis`,
      { params: httpParams },
    );
  }

  /**
   * GET /api/measurements
   *
   * Für die Detailansicht einer Station `stationId` verwenden. `stationName`
   * kann mehrere Stationen treffen, deren Werte dann vermischt zurückkommen.
   */
  searchMeasurements(
    params: MeasurementSearchParams = {},
  ): Observable<PagedResult<DailyMeasurementDto>> {
    const httpParams = buildParams({
      station_id: params.stationId,
      station_name: params.stationName,
      date_from: params.dateFrom,
      date_to: params.dateTo,
      order: params.order,
      limit: params.limit,
      offset: params.offset,
    });
    return this.http.get<PagedResult<DailyMeasurementDto>>(
      `${this.baseUrl}/measurements`,
      {
        params: httpParams,
      },
    );
  }

  /**
   * GET /api/measurements/temperature-average
   *
   * Mittelt im Backend über den kompletten Zeitraum, unabhängig von der
   * Seitengröße der Messwerttabelle.
   */
  getTemperatureAverage(
    params: TemperatureAverageParams = {},
  ): Observable<TemperatureAverageDto> {
    const httpParams = buildParams({
      station_id: params.stationId,
      station_name: params.stationName,
      date_from: params.dateFrom,
      date_to: params.dateTo,
    });
    return this.http.get<TemperatureAverageDto>(
      `${this.baseUrl}/measurements/temperature-average`,
      { params: httpParams },
    );
  }

  /**
   * GET /api/analysis/location
   *
   * Interpoliert die Werte der Nachbarstationen auf einen beliebigen Ort.
   */
  analyseLocation(
    params: LocationAnalysisParams,
  ): Observable<LocationAnalysisDto> {
    const httpParams = buildParams({
      address: params.address,
      lat: params.lat,
      lon: params.lon,
      date_from: params.dateFrom,
      date_to: params.dateTo,
      resolution: params.resolution,
      stations: params.stations,
      radius_km: params.radiusKm,
      height: params.height,
    });
    return this.http.get<LocationAnalysisDto>(
      `${this.baseUrl}/analysis/location`,
      { params: httpParams },
    );
  }
}

/** Das Backend meldet Fehler als { error: "..." }. */
export function readError(err: unknown): string {
  const body = (err as { error?: { error?: string } })?.error;
  return body?.error ?? 'Backend nicht erreichbar.';
}

/** Übernimmt nur gesetzte Werte, damit das Backend seine Standardwerte behält. */
function buildParams(
  values: Record<string, string | number | undefined>,
): HttpParams {
  let params = new HttpParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined && value !== null && value !== '') {
      params = params.set(key, String(value));
    }
  }
  return params;
}
