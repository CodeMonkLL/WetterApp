import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, Subject, catchError, switchMap, tap } from 'rxjs';

import { AnalysisChartComponent } from '../../components/analysis-chart/analysis-chart.component';
import { AnalysisTableComponent } from '../../components/analysis-table/analysis-table.component';
import { LocationSearchComponent } from '../../components/location-search/location-search.component';
import { NeighborStationsComponent } from '../../components/neighbor-stations/neighbor-stations.component';
import { LocationAnalysisDto, LocationAnalysisParams } from '../../dtos';
import {
  WeatherApiService,
  readError,
} from '../../services/weather-api.service';

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [
    LocationSearchComponent,
    NeighborStationsComponent,
    AnalysisChartComponent,
    AnalysisTableComponent,
  ],
  templateUrl: './analysis.component.html',
  styleUrl: './analysis.component.scss',
})
export class AnalysisComponent {
  private readonly api = inject(WeatherApiService);

  readonly result = signal<LocationAnalysisDto | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

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

  onSearch(params: LocationAnalysisParams): void {
    this.query.next(params);
  }
}
