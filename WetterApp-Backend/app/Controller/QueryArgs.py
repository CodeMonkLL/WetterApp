from flask import request

# Obergrenze gegen versehentliche Massenabfragen.
MAX_LIMIT = 5000


def int_arg(name: str, default: int) -> int:
    """Liest einen Query-Parameter als nicht-negative Ganzzahl.

    Raises:
        ValueError: Wenn der Wert keine Zahl oder negativ ist.
    """
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} muss eine ganze Zahl sein, war: {raw!r}") from None
    if value < 0:
        raise ValueError(f"{name} darf nicht negativ sein, war: {value}")
    return min(value, MAX_LIMIT)
