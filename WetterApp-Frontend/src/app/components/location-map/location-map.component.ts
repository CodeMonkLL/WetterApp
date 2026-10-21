import {
  Component,
  DestroyRef,
  ElementRef,
  ViewEncapsulation,
  afterNextRender,
  effect,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import * as L from 'leaflet';

import { NeighborStationDto } from '../../dtos';

export interface LatLon {
  lat: number;
  lon: number;
}

const GERMANY_CENTER: L.LatLngTuple = [51.16, 10.45];
const GERMANY_ZOOM = 6;
// 5 Nachkommastellen entsprechen rund 1 m, genauer klickt niemand.
const COORD_DECIMALS = 5;

/** OpenStreetMap-Karte, auf der per Klick ein Ort gewählt wird. */
@Component({
  selector: 'app-location-map',
  standalone: true,
  template: '<div #map class="location-map"></div>',
  styleUrl: './location-map.component.scss',
  // Leaflet erzeugt die Marker selbst, gekapselte Styles würden sie nicht erreichen.
  encapsulation: ViewEncapsulation.None,
})
export class LocationMapComponent {
  readonly point = input<LatLon | null>(null);
  /** Name des gewählten Ortes, erscheint als Beschriftung am Punkt. */
  readonly label = input<string | null>(null);
  readonly stations = input<NeighborStationDto[]>([]);
  readonly pick = output<LatLon>();

  private readonly container =
    viewChild.required<ElementRef<HTMLElement>>('map');
  private readonly map = signal<L.Map | null>(null);
  private readonly layers = L.layerGroup();

  constructor() {
    afterNextRender(() => {
      const map = L.map(this.container().nativeElement, {
        center: GERMANY_CENTER,
        zoom: GERMANY_ZOOM,
        minZoom: 5,
      });
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(map);
      this.layers.addTo(map);
      map.on('click', (e: L.LeafletMouseEvent) =>
        this.pick.emit({
          lat: round(e.latlng.lat),
          lon: round(e.latlng.lng),
        }),
      );
      this.map.set(map);
    });

    inject(DestroyRef).onDestroy(() => this.map()?.remove());

    effect(() => {
      const map = this.map();
      if (map) {
        this.draw(map, this.point(), this.label(), this.stations());
      }
    });
  }

  private draw(
    map: L.Map,
    point: LatLon | null,
    label: string | null,
    stations: NeighborStationDto[],
  ): void {
    this.layers.clearLayers();
    if (!point) {
      return;
    }
    const origin: L.LatLngTuple = [point.lat, point.lon];

    for (const s of stations) {
      const target: L.LatLngTuple = [s.latitude, s.longitude];
      L.polyline([origin, target], {
        className: 'location-map__link',
        interactive: false,
      }).addTo(this.layers);
      L.circleMarker(target, {
        className: 'location-map__station',
        radius: 6,
        fillOpacity: 1,
        // Ein Klick auf eine Station soll keinen neuen Ort auswählen.
        bubblingMouseEvents: false,
      })
        .bindTooltip(
          text(
            `${s.name}: ${s.distance_km.toFixed(1)} km, ${Math.round(s.weight * 100)} %`,
          ),
        )
        .addTo(this.layers);
    }

    const marker = L.circleMarker(origin, {
      className: 'location-map__point',
      radius: 8,
      fillOpacity: 1,
      interactive: false,
    }).addTo(this.layers);
    if (label) {
      marker
        .bindTooltip(text(label), {
          permanent: true,
          direction: 'top',
          offset: [0, -10],
          className: 'location-map__label',
        })
        .openTooltip();
    }

    if (stations.length) {
      map.fitBounds(
        L.latLngBounds([
          origin,
          ...stations.map((s): L.LatLngTuple => [s.latitude, s.longitude]),
        ]),
        { padding: [32, 32], maxZoom: 11 },
      );
    }
  }
}

function round(value: number): number {
  return +value.toFixed(COORD_DECIMALS);
}

/** Leaflet setzt Tooltip-Strings als HTML, Stationsnamen daher als Textknoten. */
function text(value: string): HTMLElement {
  const el = document.createElement('span');
  el.textContent = value;
  return el;
}
