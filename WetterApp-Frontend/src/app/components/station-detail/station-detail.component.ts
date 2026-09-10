import { Component, input } from '@angular/core';

import { StationDto, StationOverviewDto } from '../../dtos';

@Component({
  selector: 'app-station-detail',
  standalone: true,
  templateUrl: './station-detail.component.html',
  styleUrl: './station-detail.component.scss',
})
export class StationDetailComponent {
  readonly station = input<StationDto | null>(null);
  readonly overview = input<StationOverviewDto | null>(null);

  /** Stammdaten sagen, wann der DWD gemessen hat - das hier, was importiert ist. */
  hasData(): boolean {
    return !!this.overview()?.data_from;
  }
}
