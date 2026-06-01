"""
zoro_eda.classify
=================
Signal classification logic — importable by both the CLI script and tests.

This module is intentionally thin: it converts a filename string to a
``SignalClassification`` dataclass using rules from ``signal_rules.py``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields as dc_fields

from zoro_eda.signal_rules import DIRECT_MAP, PATTERN_RULES, ClassificationTuple


@dataclass
class SignalClassification:
    """One classified signal row.  Mirrors the output CSV schema."""

    file_name:             str
    signal_name:           str
    category:              str
    english_meaning:       str
    unit_hypothesis:       str
    confidence:            str
    sample_val_min:        str
    sample_val_max:        str
    exclude:               bool
    zoro_device_id_suffix: str
    zoro_metric:           str
    zoro_unit:             str
    use_energy:            bool
    use_hvac:              bool
    use_heatpump:          bool
    use_pv:                bool
    use_battery:           bool
    use_weather:           bool
    use_fdd:               bool
    use_mpc:               bool

    @classmethod
    def field_names(cls) -> list[str]:
        return [f.name for f in dc_fields(cls)]

    def to_dict(self) -> dict:
        return asdict(self)


_UNKNOWN_TUPLE: ClassificationTuple = (
    "unknown", "No rule matched — manual review needed", "", "low",
    None, None, None, False, [],
)


def _build_from_tuple(
    signal_name: str,
    filename: str,
    tup: ClassificationTuple,
    sample_min: str = "",
    sample_max: str = "",
) -> SignalClassification:
    (category, english, unit, confidence,
     device_suffix, metric, zoro_unit,
     exclude, use_cases) = tup

    return SignalClassification(
        file_name=filename,
        signal_name=signal_name,
        category=category,
        english_meaning=english,
        unit_hypothesis=unit,
        confidence=confidence,
        sample_val_min=sample_min,
        sample_val_max=sample_max,
        exclude=exclude,
        zoro_device_id_suffix=device_suffix or "",
        zoro_metric=metric or "",
        zoro_unit=zoro_unit or "",
        use_energy="energy"   in use_cases,
        use_hvac="hvac"       in use_cases,
        use_heatpump="heatpump" in use_cases,
        use_pv="pv"           in use_cases,
        use_battery="battery" in use_cases,
        use_weather="weather" in use_cases,
        use_fdd="fdd"         in use_cases,
        use_mpc="mpc"         in use_cases,
    )


def classify_signal(filename: str) -> SignalClassification:
    """Return a ``SignalClassification`` for one CSV file.

    Tries DIRECT_MAP first, then PATTERN_RULES, then falls back to unknown.
    """
    stem = filename.removesuffix(".csv")

    if stem in DIRECT_MAP:
        return _build_from_tuple(stem, filename, DIRECT_MAP[stem])

    stem_lower = stem.lower()
    for substrings, classification_tuple in PATTERN_RULES:
        if all(pattern.lower() in stem_lower for pattern in substrings):
            return _build_from_tuple(stem, filename, classification_tuple)

    return _build_from_tuple(stem, filename, _UNKNOWN_TUPLE)
