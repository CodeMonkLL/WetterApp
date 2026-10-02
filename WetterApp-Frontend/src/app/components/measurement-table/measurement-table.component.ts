import { Component, input, output } from '@angular/core';

import {
  DailyMeasurementDto,
  PagedResult,
  TemperatureAverageDto,
} from '../../dtos';

@Component({
  selector: 'app-measurement-table',
  standalone: true,
  templateUrl: './measurement-table.component.html',
  styleUrl: './measurement-table.component.scss',
})
export class MeasurementTableComponent {
  readonly result = input<PagedResult<DailyMeasurementDto> | null>(null);
  readonly average = input<TemperatureAverageDto | null>(null);
  readonly loading = input(false);
  /** Gesuchter Zeitraum lag neben dem Bestand, gezeigt wird stattdessen alles. */
  readonly periodWithoutData = input(false);
  readonly pageChange = output<number>();

  /** Zeigt eine Temperatur mit einer Nachkommastelle, sonst "-". */
  formatTemperature(value: number | null | undefined): string {
    return value === null || value === undefined
      ? '-'
      : `${value.toFixed(1)} \u00b0C`;
  }

  /** Gesuchter Zeitraum, ohne Datumsfilter der gesamte Bestand. */
  periodLabel(): string {
    const avg = this.average();
    if (!avg) {
      return '';
    }
    if (avg.date_from && avg.date_to) {
      return `${formatDate(avg.date_from)} bis ${formatDate(avg.date_to)}`;
    }
    return 'gesamter Zeitraum';
  }

  /** Meldet Lücken: Die Station deckt den gesuchten Zeitraum nicht komplett ab. */
  dataDiffersFromPeriod(): boolean {
    const avg = this.average();
    if (!avg?.date_from || !avg?.date_to) {
      return false;
    }
    return avg.data_from !== avg.date_from || avg.data_to !== avg.date_to;
  }

  dataRangeLabel(): string {
    const avg = this.average();
    if (!avg?.data_from || !avg?.data_to) {
      return '';
    }
    return `${formatDate(avg.data_from)} bis ${formatDate(avg.data_to)}`;
  }

  previousPage(): void {
    const page = this.result();
    if (page) {
      this.pageChange.emit(Math.max(0, page.offset - page.limit));
    }
  }

  nextPage(): void {
    const page = this.result();
    if (page) {
      this.pageChange.emit(page.offset + page.limit);
    }
  }

  hasPrevious(): boolean {
    const page = this.result();
    return !!page && page.offset > 0;
  }

  hasNext(): boolean {
    const page = this.result();
    return !!page && page.offset + page.limit < page.total;
  }
}

/** Wandelt das ISO-Datum des Backends in die deutsche Schreibweise. */
function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-');
  return `${day}.${month}.${year}`;
}
