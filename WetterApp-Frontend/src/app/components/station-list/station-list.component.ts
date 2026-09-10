import { Component, input, output } from '@angular/core';

import { PagedResult, StationDto } from '../../dtos';

@Component({
  selector: 'app-station-list',
  standalone: true,
  templateUrl: './station-list.component.html',
  styleUrl: './station-list.component.scss',
})
export class StationListComponent {
  readonly result = input<PagedResult<StationDto> | null>(null);
  readonly loading = input(false);
  readonly selectedId = input<string | null>(null);
  readonly select = output<StationDto>();
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
