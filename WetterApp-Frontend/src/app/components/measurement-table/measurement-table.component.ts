import { Component, input, output } from '@angular/core';

import { DailyMeasurementDto, PagedResult } from '../../dtos';

@Component({
  selector: 'app-measurement-table',
  standalone: true,
  templateUrl: './measurement-table.component.html',
  styleUrl: './measurement-table.component.scss',
})
export class MeasurementTableComponent {
  readonly result = input<PagedResult<DailyMeasurementDto> | null>(null);
  readonly loading = input(false);
  readonly pageChange = output<number>();

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
