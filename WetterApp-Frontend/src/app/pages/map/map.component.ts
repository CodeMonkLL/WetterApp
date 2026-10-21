import { Component, computed, inject, signal, viewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, Subject, catchError, switchMap, tap } from 'rxjs';

import { AnalysisChartComponent } from '../../components/analysis-chart/analysis-chart.component';
import { AnalysisTableComponent } from '../../components/analysis-table/analysis-table.component';
import {
  LatLon,
  LocationMapComponent,
} from '../../components/location-map/location-map.component';
import { LocationSearchComponent } from '../../components/location-search/location-search.component';
import { NeighborStationsComponent } from '../../components/neighbor-stations/neighbor-stations.component';
import {
  LocationAnalysisDto,
  LocationAnalysisParams,
  NeighborStationDto,
} from '../../dtos';
import {
  WeatherApiService,
  readError,
} from '../../services/weather-api.service';

const NO_STATIONS: NeighborStationDto[] = [];

/** Ortsauswertung per Klick auf die Karte statt per Adresse. */
@Component({
  selector: 'app-map',
  standalone: true,
  imports: [
    LocationSearchComponent,
    LocationMapComponent,
    NeighborStationsComponent,
    AnalysisChartComponent,
    AnalysisTableComponent,
  ],
  templateUrl: './map.component.html',
  styleUrl: './map.component.scss',
})
export class MapComponent {
  private readonly api = inject(WeatherApiService);
  private readonly settings = viewChild.required(LocationSearchComponent);

  readonly point = signal<LatLon | null>(null);
  readonly result = signal<LocationAnalysisDto | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly stations = computed(() => this.result()?.stations ?? NO_STATIONS);

  private readonly query = new Subject<LocationAnalysisParams>();

  constructor() {
    this.query
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set(null);
        }),
        switchMap((params) =>
          this.api.analyseLocation(params).pipe(
            catchError((err) => {
              this.error.set(readError(err));
              this.result.set(null);
              this.loading.set(false);
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((result) => {
        this.result.set(result);
        this.loading.set(false);
      });
  }

  onPick(point: LatLon): void {
    this.point.set(point);
    // Alte Stationen sollen nicht um den neuen Punkt herum stehen bleiben.
    this.result.set(null);
    this.analyse(this.settings().params());
  }

  onSearch(params: LocationAnalysisParams): void {
    this.analyse(params);
  }

  private analyse(params: LocationAnalysisParams): void {
    const point = this.point();
    if (point) {
      this.query.next({ ...params, lat: point.lat, lon: point.lon });
    }
  }
}
