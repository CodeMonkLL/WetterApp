from dataclasses import dataclass

from app.Model.DailyMesaurement import DailyMeasurement


@dataclass(frozen=True)
class DailyMeasurementDto:
    """Ein Tageswert einer Station. `date` ist ein ISO-String (YYYY-MM-DD)."""

    station_id: str
    date: str

    qn3: int | None      # Qualitätsniveau Winddaten
    qn4: int | None      # Qualitätsniveau übrige Daten
    fx: float | None     # Windspitze (m/s)
    fm: float | None     # Tagesmittel Wind (m/s)
    rsk: float | None    # Niederschlagshöhe (mm)
    rskf: int | None     # Niederschlagsform
    shk_tag: int | None  # Schneehöhe (cm)
    sdk: float | None    # Sonnenscheindauer (h)
    nm: float | None     # Bedeckungsgrad (1/8)
    vpm: float | None    # Dampfdruck (hPa)
    pm: float | None     # Luftdruck (hPa)
    tmk: float | None    # Tagesmittel Temperatur (°C)
    upm: float | None    # Relative Feuchte (%)
    txk: float | None    # Tagesmaximum (°C)
    tnk: float | None    # Tagesminimum (°C)
    tgk: float | None    # Minimum 5 cm über Boden (°C)

    @classmethod
    def from_entity(cls, measurement: DailyMeasurement) -> "DailyMeasurementDto":
        return cls(
            station_id=measurement.station_id,
            date=measurement.date.isoformat(),
            qn3=measurement.qn3,
            qn4=measurement.qn4,
            fx=measurement.fx,
            fm=measurement.fm,
            rsk=measurement.rsk,
            rskf=measurement.rskf,
            shk_tag=measurement.shk_tag,
            sdk=measurement.sdk,
            nm=measurement.nm,
            vpm=measurement.vpm,
            pm=measurement.pm,
            tmk=measurement.tmk,
            upm=measurement.upm,
            txk=measurement.txk,
            tnk=measurement.tnk,
            tgk=measurement.tgk,
        )
