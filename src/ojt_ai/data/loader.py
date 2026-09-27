"""Load a prepared five-table CSV directory."""
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .validator import DataError, SCHEMA, KEYS, NUMBERS, validate_relations

def load_data(directory):
    """Reject invalid batches; tolerate extra columns. Headers required for empty tables."""
    tables, warnings = {}, []
    for table, fields in SCHEMA.items():
        path = Path(directory) / ("student.csv" if table == "students" else f"{table}.csv")
        if table == "students" and not path.exists():
            path = Path(directory) / "students.csv"
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)):
                raise DataError(f"{path.name}: duplicate headers")
            missing = set(fields.split()) - set(headers)
            if missing:
                raise DataError(f"{path.name}: missing columns {sorted(missing)}")
            extra = set(headers) - set(fields.split())
            if extra:
                warnings.append(f"{path.name}: unused columns {sorted(extra)}")
            rows, seen = [], set()
            for line, raw in enumerate(reader, 2):
                context = f"{path.name}:{line}"
                if None in raw:
                    raise DataError(f"{context}: too many CSV fields")
                row = {key: (raw.get(key) or "").strip() for key in fields.split()}
                for key, value in row.items():
                    if not value and key != "email":
                        raise DataError(f"{context}: empty {key}")
                for key in NUMBERS.get(table, ()):
                    try:
                        value = Decimal(row[key])
                    except InvalidOperation as exc:
                        raise DataError(f"{context}: invalid number {key}") from exc
                    if not value.is_finite() or value < 0:
                        raise DataError(f"{context}: invalid nonnegative number {key}")
                    if key in ("current_semester", "recommended_semester", "semester_number"):
                        minimum = 0 if key == "recommended_semester" else 1
                        if value < minimum or value != int(value):
                            raise DataError(f"{context}: {key} must be an integer >= {minimum}")
                    row[key] = value
                identity = tuple(row[key] for key in KEYS[table])
                if identity in seen:
                    raise DataError(f"{context}: duplicate key {identity}")
                seen.add(identity)
                rows.append(row)
            tables[table] = rows
    validate_relations(tables)
    return tables, warnings


