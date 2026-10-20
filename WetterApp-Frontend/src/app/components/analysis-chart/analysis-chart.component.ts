import { Component, computed, input } from '@angular/core';

import { AnalysisPeriodDto } from '../../dtos';
import { formatPeriod } from '../analysis-table/analysis-table.component';

const WIDTH = 640;
const PAD = { top: 8, right: 8, bottom: 20, left: 40 };
const TEMP_HEIGHT = 220;
const RAIN_HEIGHT = 120;
const X_LABELS = 6;
// Darüber liegen die Punkte so dicht, dass sie nur noch die Linie verdecken.
const MAX_MARKERS = 60;
// Darüber werden die Balken als ein einziger Pfad gezeichnet, sonst wird das DOM zu groß.
const MAX_BAR_ELEMENTS = 400;

interface Tick {
  y: number;
  label: string;
}

interface XLabel {
  x: number;
  label: string;
  anchor: 'start' | 'middle' | 'end';
}

interface Marker {
  x: number;
  y: number;
  title: string;
}

interface Bar {
  x: number;
  y: number;
  width: number;
  height: number;
  title: string;
}

interface TemperatureChart {
  ticks: Tick[];
  lines: { cls: string; path: string }[];
  markers: Marker[];
}

interface RainChart {
  ticks: Tick[];
  /** Einzelbalken mit Tooltip, leer bei langen Reihen. */
  bars: Bar[];
  /** Alle Balken als ein Pfad, leer bei kurzen Reihen. */
  barPath: string;
}

/** Temperaturverlauf als Linien und Niederschlag als Balken, als reines SVG. */
@Component({
  selector: 'app-analysis-chart',
  standalone: true,
  templateUrl: './analysis-chart.component.html',
  styleUrl: './analysis-chart.component.scss',
})
export class AnalysisChartComponent {
  readonly series = input<AnalysisPeriodDto[]>([]);

  readonly width = WIDTH;
  readonly pad = PAD;
  readonly tempHeight = TEMP_HEIGHT;
  readonly rainHeight = RAIN_HEIGHT;

  /** Jeder Zeitraum bekommt ein gleich breites Band, x ist dessen Mitte. */
  private readonly xs = computed(() => {
    const n = this.series().length;
    const band = (WIDTH - PAD.left - PAD.right) / Math.max(n, 1);
    return this.series().map((_, i) => PAD.left + (i + 0.5) * band);
  });

  readonly xLabels = computed<XLabel[]>(() => {
    const series = this.series();
    const xs = this.xs();
    const n = series.length;
    if (!n) {
      return [];
    }
    const count = Math.min(X_LABELS, n);
    const indices =
      count === 1
        ? [0]
        : [
            ...new Set(
              Array.from({ length: count }, (_, k) =>
                Math.round((k * (n - 1)) / (count - 1)),
              ),
            ),
          ];
    return indices.map((i, k) => ({
      x: xs[i],
      label: formatPeriod(series[i].period),
      anchor:
        indices.length === 1
          ? 'middle'
          : k === 0
            ? 'start'
            : k === indices.length - 1
              ? 'end'
              : 'middle',
    }));
  });

  readonly temperature = computed<TemperatureChart | null>(() => {
    const series = this.series();
    const range = extent(series.flatMap((p) => [p.txk, p.tmk, p.tnk]));
    if (!range) {
      return null;
    }
    const min = Math.floor(range.min / 5) * 5;
    const max = Math.max(Math.ceil(range.max / 5) * 5, min + 5);
    const y = (v: number) => scale(v, min, max, TEMP_HEIGHT);
    const xs = this.xs();

    const step = max - min > 30 ? 10 : 5;
    const ticks: Tick[] = [];
    for (let v = min; v <= max; v += step) {
      ticks.push({ y: y(v), label: `${v}\u00b0` });
    }

    return {
      ticks,
      lines: [
        {
          cls: 'line--max',
          path: linePath(
            xs,
            series.map((p) => p.txk),
            y,
          ),
        },
        {
          cls: 'line--min',
          path: linePath(
            xs,
            series.map((p) => p.tnk),
            y,
          ),
        },
        {
          cls: 'line--mean',
          path: linePath(
            xs,
            series.map((p) => p.tmk),
            y,
          ),
        },
      ],
      markers:
        series.length > MAX_MARKERS
          ? []
          : series.flatMap((p, i) =>
              p.tmk === null
                ? []
                : [
                    {
                      x: xs[i],
                      y: y(p.tmk),
                      title: `${formatPeriod(p.period)}: ${p.tmk.toFixed(1)} \u00b0C`,
                    },
                  ],
            ),
    };
  });

  readonly rain = computed<RainChart | null>(() => {
    const series = this.series();
    const range = extent(series.map((p) => p.rsk));
    if (!range) {
      return null;
    }
    const max = niceCeil(range.max);
    const y = (v: number) => scale(v, 0, max, RAIN_HEIGHT);
    const xs = this.xs();
    const band = (WIDTH - PAD.left - PAD.right) / series.length;
    const width = Math.max(1, band * 0.8);
    const base = y(0);
    const bars: Bar[] = series.flatMap((p, i) =>
      p.rsk === null
        ? []
        : [
            {
              x: xs[i] - width / 2,
              y: y(p.rsk),
              width,
              height: base - y(p.rsk),
              title: `${formatPeriod(p.period)}: ${p.rsk.toFixed(1)} mm`,
            },
          ],
    );
    const asPath = bars.length > MAX_BAR_ELEMENTS;

    return {
      ticks: [0, max / 2, max].map((v) => ({
        y: y(v),
        label: String(+v.toFixed(1)),
      })),
      bars: asPath ? [] : bars,
      barPath: asPath
        ? bars
            .map(
              (b) =>
                `M${b.x.toFixed(2)},${base.toFixed(1)}v${(-b.height).toFixed(1)}h${b.width.toFixed(2)}v${b.height.toFixed(1)}z`,
            )
            .join('')
        : '',
    };
  });
}

/** Ohne Spread, weil Tagesreihen über Jahrzehnte das Argumentlimit sprengen. */
function extent(
  values: (number | null)[],
): { min: number; max: number } | null {
  let min = Infinity;
  let max = -Infinity;
  for (const v of values) {
    if (v !== null) {
      min = Math.min(min, v);
      max = Math.max(max, v);
    }
  }
  return min === Infinity ? null : { min, max };
}

function scale(v: number, min: number, max: number, height: number): number {
  const plot = height - PAD.top - PAD.bottom;
  return PAD.top + (1 - (v - min) / (max - min)) * plot;
}

/** Rundet auf eine glatte Achsengrenze, z.B. 87 -> 90, 1234 -> 2000. */
function niceCeil(value: number): number {
  if (value <= 0) {
    return 1;
  }
  const magnitude = 10 ** Math.floor(Math.log10(value));
  return Math.ceil(value / magnitude) * magnitude;
}

/** Fehlende Werte unterbrechen die Linie, statt sie zu überbrücken. */
function linePath(
  xs: number[],
  values: (number | null)[],
  y: (v: number) => number,
): string {
  let d = '';
  let penDown = false;
  values.forEach((v, i) => {
    if (v === null) {
      penDown = false;
      return;
    }
    d += `${penDown ? 'L' : 'M'}${xs[i].toFixed(1)},${y(v).toFixed(1)}`;
    penDown = true;
  });
  return d;
}
