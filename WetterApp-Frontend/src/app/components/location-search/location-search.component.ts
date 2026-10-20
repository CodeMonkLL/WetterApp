import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AnalysisResolution, LocationAnalysisParams } from '../../dtos';

// Das historische DWD-Archiv reicht bis zum Ende des Vorjahres.
const LAST_FULL_YEAR = new Date().getFullYear() - 1;

@Component({
  selector: 'app-location-search',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './location-search.component.html',
  styleUrl: './location-search.component.scss',
})
export class LocationSearchComponent {
  readonly loading = input(false);
  readonly search = output<LocationAnalysisParams>();

  address = '';
  dateFrom = `${LAST_FULL_YEAR - 9}-01-01`;
  dateTo = `${LAST_FULL_YEAR}-12-31`;
  resolution: AnalysisResolution = 'month';
  stations: number | null = 5;
  radiusKm: number | null = 50;
  height: number | null = null;

  submit(): void {
    this.search.emit({
      address: this.address.trim(),
      dateFrom: this.dateFrom,
      dateTo: this.dateTo,
      resolution: this.resolution,
      stations: this.stations ?? undefined,
      radiusKm: this.radiusKm ?? undefined,
      height: this.height ?? undefined,
    });
  }
}
