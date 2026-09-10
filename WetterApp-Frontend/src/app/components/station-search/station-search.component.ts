import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { StationSearchParams } from '../../dtos';

@Component({
  selector: 'app-station-search',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './station-search.component.html',
  styleUrl: './station-search.component.scss',
})
export class StationSearchComponent {
  readonly states = input<string[]>([]);
  readonly loading = input(false);
  readonly search = output<StationSearchParams>();

  name = '';
  state = '';
  dateFrom = '';
  dateTo = '';

  submit(): void {
    this.search.emit({
      name: this.name.trim() || undefined,
      state: this.state || undefined,
      dateFrom: this.dateFrom || undefined,
      dateTo: this.dateTo || undefined,
    });
  }

  reset(): void {
    this.name = '';
    this.state = '';
    this.dateFrom = '';
    this.dateTo = '';
    this.submit();
  }
}
