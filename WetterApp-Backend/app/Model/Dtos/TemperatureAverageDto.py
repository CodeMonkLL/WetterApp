from dataclasses import dataclass


@dataclass(frozen=True)
class TemperatureAverageDto:
    """Mittlere Temperaturen über einen Zeitraum.

    `date_from`/`date_to` spiegeln die Filtereingabe, `data_from`/`data_to` den
    Zeitraum, für den tatsächlich Messwerte vorliegen. Beides kann abweichen,
    wenn die Station im angefragten Zeitraum Lücken hat.
    `days` zählt nur Tage mit vorhandenem Tagesmittel. Ohne Treffer sind alle
    Werte null.
    """

    station_id: str | None
    date_from: str | None
    date_to: str | None
    data_from: str | None
    data_to: str | None
    days: int

    avg_tmk: float | None  # Mittel der Tagesmittel (°C)
    avg_txk: float | None  # Mittel der Tagesmaxima (°C)
    avg_tnk: float | None  # Mittel der Tagesminima (°C)
