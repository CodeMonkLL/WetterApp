import { Component, computed, input, linkedSignal } from '@angular/core';

import { AnalysisPeriodDto } from '../../dtos';

const PAGE_SIZE = 100;

@Component({
  selector: 'app-analysis-table',
  standalone: true,
  templateUrl: './analysis-table.component.html',
  styleUrl: './analysis-table.component.scss',
})
export class AnalysisTableComponent {
  readonly series = input<AnalysisPeriodDto[]>([]);

  /** Springt bei jedem neuen Ergebnis auf die erste Seite zurück. */
  readonly offset = linkedSignal({ source: this.series, computation: () => 0 });

  readonly page = computed(() =>
    this.series().slice(this.offset(), this.offset() + PAGE_SIZE),
  );
  readonly hasPrevious = computed(() => this.offset() > 0);
  readonly hasNext = computed(
    () => this.offset() + PAGE_SIZE < this.series().length,
  );
  readonly rangeLabel = computed(() => {
    const total = this.series().length;
    const end = Math.min(this.offset() + PAGE_SIZE, total);
    return `${this.offset() + 1}-${end} von ${total}`;
  });

  readonly formatPeriod = formatPeriod;

  format(value: number | null): string {
    return value === null ? '-' : value.toFixed(1);
  }

  previousPage(): void {
    this.offset.update((offset) => Math.max(0, offset - PAGE_SIZE));
  }

  nextPage(): void {
    this.offset.update((offset) => offset + PAGE_SIZE);
  }
}

/** "2020-01-05" -> "05.01.2020", "2020-01" -> "01.2020", "2020" bleibt. */
export function formatPeriod(period: string): string {
  return period.split('-').reverse().join('.');
}
