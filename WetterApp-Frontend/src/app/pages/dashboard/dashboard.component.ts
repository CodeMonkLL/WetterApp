import {
  Component,
  OnInit,
  WritableSignal,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, Observable, Subject, catchError, switchMap, tap } from 'rxjs';

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
  TemperatureAverageDto,
} from '../../dtos';
import { WeatherApiService } from '../../services/weather-api.service';

const STATION_PAGE_SIZE = 25;
const MEASUREMENT_PAGE_SIZE = 50;

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
  readonly overviewLoading = signal(false);

  readonly measurements = signal<PagedResult<DailyMeasurementDto> | null>(null);
  readonly measurementsLoading = signal(false);
  readonly temperatureAverage = signal<TemperatureAverageDto | null>(null);
  /** Gesuchter Zeitraum liegt komplett neben dem importierten Bestand. */
  readonly periodWithoutData = signal(false);

  readonly error = signal<string | null>(null);

  private readonly searchParams = signal<StationSearchParams>({});
  /** Zeitraum der Messwerte, bereits gegen den importierten Bestand geprüft. */
  private readonly measurementRange = signal<DateRange>({});

  private readonly stationQuery = new Subject<number>();
  private readonly overviewQuery = new Subject<string>();
  private readonly measurementQuery = new Subject<number>();
  private readonly averageQuery = new Subject<void>();

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
    // tatsächlich importiert ist und für die Messwerte taugt.
    this.overviewQuery
      .pipe(
        tap(() => {
          this.overviewLoading.set(true);
          this.measurementsLoading.set(true);
        }),
        switchMap((stationId) =>
          this.api
            .getStationOverview(stationId)
            .pipe(
              catchError((err) =>
                this.fail(err, this.overviewLoading, this.measurementsLoading),
              ),
            ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((overview) => {
        this.overview.set(overview);
        this.overviewLoading.set(false);
        this.applyRange(overview);
        this.measurementQuery.next(0);
        this.averageQuery.next();
      });

    this.measurementQuery
      .pipe(
        tap(() => this.measurementsLoading.set(true)),
        switchMap((offset) => {
          const station = this.selected();
          if (!station) {
            this.measurementsLoading.set(false);
            return EMPTY;
          }
          return this.api
            .searchMeasurements({
              stationId: station.station_id,
              ...this.measurementRange(),
              limit: MEASUREMENT_PAGE_SIZE,
              offset,
            })
            .pipe(
              catchError((err) => this.fail(err, this.measurementsLoading)),
            );
        }),
        takeUntilDestroyed(),
      )
      .subscribe((result) => {
        this.measurements.set(result);
        this.measurementsLoading.set(false);
      });

    // Gilt für den gesamten Zeitraum, muss daher nicht je Tabellenseite neu laden.
    this.averageQuery
      .pipe(
        switchMap(() => {
          const station = this.selected();
          if (!station) {
            return EMPTY;
          }
          return this.api
            .getTemperatureAverage({
              stationId: station.station_id,
              ...this.measurementRange(),
            })
            .pipe(catchError((err) => this.fail(err)));
        }),
        takeUntilDestroyed(),
      )
      .subscribe((average) => this.temperatureAverage.set(average));
  }

  ngOnInit(): void {
    this.api.listStates().subscribe({
      next: (states) => this.states.set(states),
      error: () => this.states.set([]),
    });
    this.loadStations(0);
  }

  onSearch(params: StationSearchParams): void {
    this.searchParams.set(params);
    this.selected.set(null);
    this.overview.set(null);
    this.overviewLoading.set(false);
    this.measurements.set(null);
    this.measurementsLoading.set(false);
    this.temperatureAverage.set(null);
    this.periodWithoutData.set(false);
    this.loadStations(0);
  }

  onSelectStation(station: StationDto): void {
    this.selected.set(station);
    this.overview.set(null);
    this.measurements.set(null);
    this.temperatureAverage.set(null);
    this.periodWithoutData.set(false);
    this.error.set(null);

    this.overviewQuery.next(station.station_id);
  }

  loadStations(offset: number): void {
    this.stationQuery.next(offset);
  }

  loadMeasurements(offset: number): void {
    this.measurementQuery.next(offset);
  }

  /**
   * Die Stationssuche filtert über die DWD-Stammdaten, die Messwerte über den
   * importierten Bestand. Liegt der gesuchte Zeitraum komplett daneben, würde
   * der Filter eine leere Tabelle erzeugen - dann lieber den ganzen Bestand.
   */
  private applyRange(overview: StationOverviewDto): void {
    const { dateFrom, dateTo } = this.searchParams();
    const dataFrom = overview.data_from;
    const dataTo = overview.data_to;

    if ((!dateFrom && !dateTo) || !dataFrom || !dataTo) {
      this.measurementRange.set({});
      this.periodWithoutData.set(false);
      return;
    }

    // ISO-Datumsstrings lassen sich direkt vergleichen.
    const overlaps =
      (!dateFrom || dateFrom <= dataTo) && (!dateTo || dateTo >= dataFrom);
    this.measurementRange.set(overlaps ? { dateFrom, dateTo } : {});
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

/** Das Backend meldet Eingabefehler als { error: "..." } mit Status 400. */
function readError(err: unknown): string {
  const body = (err as { error?: { error?: string } })?.error;
  return body?.error ?? 'Backend nicht erreichbar.';
}
