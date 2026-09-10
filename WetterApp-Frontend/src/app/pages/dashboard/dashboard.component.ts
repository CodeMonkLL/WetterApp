import { Component, OnInit, inject, signal } from '@angular/core';

import { MeasurementTableComponent } from '../../components/measurement-table/measurement-table.component';
import { StationDetailComponent } from '../../components/station-detail/station-detail.component';
import { StationListComponent } from '../../components/station-list/station-list.component';
import { StationSearchComponent } from '../../components/station-search/station-search.component';
import {
  DailyMeasurementDto,
  PagedResult,
  StationDto,
  StationOverviewDto,
  StationSearchParams,
} from '../../dtos';
import { WeatherApiService } from '../../services/weather-api.service';

const STATION_PAGE_SIZE = 25;
const MEASUREMENT_PAGE_SIZE = 50;

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    StationSearchComponent,
    StationListComponent,
    StationDetailComponent,
    MeasurementTableComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(WeatherApiService);

  readonly states = signal<string[]>([]);
  readonly stations = signal<PagedResult<StationDto> | null>(null);
  readonly stationsLoading = signal(false);

  readonly selected = signal<StationDto | null>(null);
  readonly overview = signal<StationOverviewDto | null>(null);

  readonly measurements = signal<PagedResult<DailyMeasurementDto> | null>(null);
  readonly measurementsLoading = signal(false);

  readonly error = signal<string | null>(null);

  private params: StationSearchParams = {};

  ngOnInit(): void {
    this.api.listStates().subscribe({
      next: (states) => this.states.set(states),
      error: () => this.states.set([]),
    });
    this.loadStations(0);
  }

  onSearch(params: StationSearchParams): void {
    this.params = params;
    this.selected.set(null);
    this.overview.set(null);
    this.measurements.set(null);
    this.loadStations(0);
  }

  onSelectStation(station: StationDto): void {
    this.selected.set(station);
    this.overview.set(null);

    this.api.getStationOverview(station.station_id).subscribe({
      next: (overview) => this.overview.set(overview),
      error: (err) => this.error.set(readError(err)),
    });
    this.loadMeasurements(0);
  }

  loadStations(offset: number): void {
    this.stationsLoading.set(true);
    this.error.set(null);

    this.api
      .searchStations({ ...this.params, limit: STATION_PAGE_SIZE, offset })
      .subscribe({
        next: (result) => {
          this.stations.set(result);
          this.stationsLoading.set(false);
        },
        error: (err) => {
          this.error.set(readError(err));
          this.stationsLoading.set(false);
        },
      });
  }

  loadMeasurements(offset: number): void {
    const station = this.selected();
    if (!station) {
      return;
    }

    this.measurementsLoading.set(true);
    this.api
      .searchMeasurements({
        stationId: station.station_id,
        dateFrom: this.params.dateFrom,
        dateTo: this.params.dateTo,
        limit: MEASUREMENT_PAGE_SIZE,
        offset,
      })
      .subscribe({
        next: (result) => {
          this.measurements.set(result);
          this.measurementsLoading.set(false);
        },
        error: (err) => {
          this.error.set(readError(err));
          this.measurementsLoading.set(false);
        },
      });
  }
}

/** Das Backend meldet Eingabefehler als { error: "..." } mit Status 400. */
function readError(err: unknown): string {
  const body = (err as { error?: { error?: string } })?.error;
  return body?.error ?? 'Backend nicht erreichbar.';
}
