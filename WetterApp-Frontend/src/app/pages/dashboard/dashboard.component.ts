import {
  Component,
  OnInit,
  WritableSignal,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, Observable, Subject, catchError, switchMap, tap } from 'rxjs';

import { AnalysisChartComponent } from '../../components/analysis-chart/analysis-chart.component';
import { AnalysisTableComponent } from '../../components/analysis-table/analysis-table.component';
import { StationDetailComponent } from '../../components/station-detail/station-detail.component';
import { StationListComponent } from '../../components/station-list/station-list.component';
import { StationSearchComponent } from '../../components/station-search/station-search.component';
import {
  AnalysisResolution,
  PagedResult,
  StationAnalysisDto,
  StationDto,
  StationOverviewDto,
  StationSearchParams,
} from '../../dtos';
import {
  WeatherApiService,
  readError,
} from '../../services/weather-api.service';

const STATION_PAGE_SIZE = 25;

interface DateRange {
  dateFrom?: string;
  dateTo?: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    StationSearchComponent,
    StationListComponent,
    StationDetailComponent,
    AnalysisChartComponent,
    AnalysisTableComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(WeatherApiService);

  readonly resolutions: { value: AnalysisResolution; label: string }[] = [
    { value: 'day', label: 'Tag' },
    { value: 'month', label: 'Monat' },
    { value: 'year', label: 'Jahr' },
  ];

  readonly stations = signal<PagedResult<StationDto> | null>(null);
  readonly stationsLoading = signal(false);

  readonly selected = signal<StationDto | null>(null);
  readonly overview = signal<StationOverviewDto | null>(null);
  readonly overviewLoading = signal(false);

  readonly analysis = signal<StationAnalysisDto | null>(null);
  readonly analysisLoading = signal(false);
  readonly resolution = signal<AnalysisResolution>('month');
  /** Gesuchter Zeitraum liegt komplett neben dem importierten Bestand. */
  readonly periodWithoutData = signal(false);

  readonly error = signal<string | null>(null);

  private readonly searchParams = signal<StationSearchParams>({});
  /** Zeitraum der Auswertung, bereits gegen den importierten Bestand geprüft. */
  private readonly analysisRange = signal<DateRange>({});

  private readonly stationQuery = new Subject<number>();
  private readonly overviewQuery = new Subject<string>();
  private readonly analysisQuery = new Subject<void>();

  /** switchMap bricht die vorherige Anfrage ab, sonst kann eine überholte Antwort zuletzt gewinnen. */
  constructor() {
    this.stationQuery
      .pipe(
        tap(() => {
          this.stationsLoading.set(true);
          this.error.set(null);
        }),
        switchMap((offset) =>
          this.api
            .searchStations({
              ...this.searchParams(),
              limit: STATION_PAGE_SIZE,
              offset,
            })
            .pipe(catchError((err) => this.fail(err, this.stationsLoading))),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((result) => {
        this.stations.set(result);
        this.stationsLoading.set(false);
      });

    // Das Overview läuft zuerst, weil erst damit feststeht, welcher Zeitraum
    // tatsächlich importiert ist und für die Auswertung taugt.
    this.overviewQuery
      .pipe(
        tap(() => {
          this.overviewLoading.set(true);
          this.analysisLoading.set(true);
        }),
        switchMap((stationId) =>
          this.api
            .getStationOverview(stationId)
            .pipe(
              catchError((err) =>
                this.fail(err, this.overviewLoading, this.analysisLoading),
              ),
            ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((overview) => {
        this.overview.set(overview);
        this.overviewLoading.set(false);
        this.applyRange(overview);
        this.analysisQuery.next();
      });

    this.analysisQuery
      .pipe(
        tap(() => this.analysisLoading.set(true)),
        switchMap(() => {
          const station = this.selected();
          if (!station) {
            this.analysisLoading.set(false);
            return EMPTY;
          }
          return this.api
            .getStationAnalysis(station.station_id, {
              ...this.analysisRange(),
              resolution: this.resolution(),
            })
            .pipe(catchError((err) => this.fail(err, this.analysisLoading)));
        }),
        takeUntilDestroyed(),
      )
      .subscribe((analysis) => {
        this.analysis.set(analysis);
        this.analysisLoading.set(false);
      });
  }

  ngOnInit(): void {
    this.loadStations(0);
  }

  onSearch(params: StationSearchParams): void {
    this.searchParams.set(params);
    this.selected.set(null);
    this.overview.set(null);
    this.overviewLoading.set(false);
    this.analysis.set(null);
    this.analysisLoading.set(false);
    this.periodWithoutData.set(false);
    this.loadStations(0);
  }

  onSelectStation(station: StationDto): void {
    this.selected.set(station);
    this.overview.set(null);
    this.analysis.set(null);
    this.periodWithoutData.set(false);
    this.error.set(null);

    this.overviewQuery.next(station.station_id);
  }

  onResolutionChange(resolution: AnalysisResolution): void {
    this.resolution.set(resolution);
    this.analysisQuery.next();
  }

  /** Wandelt das ISO-Datum des Backends in die deutsche Schreibweise. */
  formatDate(isoDate: string): string {
    return isoDate.split('-').reverse().join('.');
  }

  loadStations(offset: number): void {
    this.stationQuery.next(offset);
  }

  /**
   * Die Stationssuche filtert über die DWD-Stammdaten, die Auswertung über den
   * importierten Bestand. Liegt der gesuchte Zeitraum komplett daneben, würde
   * der Filter eine leere Auswertung erzeugen - dann lieber den ganzen Bestand.
   */
  private applyRange(overview: StationOverviewDto): void {
    const { dateFrom, dateTo } = this.searchParams();
    const dataFrom = overview.data_from;
    const dataTo = overview.data_to;

    if ((!dateFrom && !dateTo) || !dataFrom || !dataTo) {
      this.analysisRange.set({});
      this.periodWithoutData.set(false);
      return;
    }

    // ISO-Datumsstrings lassen sich direkt vergleichen.
    const overlaps =
      (!dateFrom || dateFrom <= dataTo) && (!dateTo || dateTo >= dataFrom);
    this.analysisRange.set(overlaps ? { dateFrom, dateTo } : {});
    this.periodWithoutData.set(!overlaps);
  }

  private fail(
    err: unknown,
    ...loading: WritableSignal<boolean>[]
  ): Observable<never> {
    this.error.set(readError(err));
    loading.forEach((flag) => flag.set(false));
    return EMPTY;
  }
}
