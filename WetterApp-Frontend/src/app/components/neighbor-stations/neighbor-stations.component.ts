import { Component, input } from '@angular/core';

import { LocationAnalysisDto } from '../../dtos';

@Component({
  selector: 'app-neighbor-stations',
  standalone: true,
  templateUrl: './neighbor-stations.component.html',
  styleUrl: './neighbor-stations.component.scss',
})
export class NeighborStationsComponent {
  readonly analysis = input.required<LocationAnalysisDto>();

  percent(weight: number): string {
    return `${Math.round(weight * 100)} %`;
  }
}
