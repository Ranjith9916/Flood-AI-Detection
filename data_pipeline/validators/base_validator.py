"""
data_pipeline/validators/base_validator.py
Base validation framework for all data sources.
Each validator receives a raw record dict and returns a ValidationResult.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FieldError:
    field: str
    message: str
    value: Any = None
    severity: str = "ERROR"       # ERROR (reject) | WARNING (flag but keep)


@dataclass
class ValidationResult:
    is_valid: bool
    record: dict[str, Any]        # Possibly mutated (clamped, filled, flagged)
    errors: list[FieldError] = field(default_factory=list)
    warnings: list[FieldError] = field(default_factory=list)
    quality_flag: str = "OK"      # OK | SUSPECT | REJECTED

    def add_error(self, field: str, message: str, value: Any = None):
        self.errors.append(FieldError(field=field, message=message, value=value))
        self.is_valid = False
        self.quality_flag = "REJECTED"

    def add_warning(self, field: str, message: str, value: Any = None):
        self.warnings.append(
            FieldError(field=field, message=message, value=value, severity="WARNING")
        )
        if self.quality_flag == "OK":
            self.quality_flag = "SUSPECT"


class BaseValidator:
    """
    Validates a single record dict and returns a ValidationResult.
    Subclass and override validate() for each data type.
    """

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        raise NotImplementedError

    def validate_batch(
        self, records: list[dict[str, Any]]
    ) -> tuple[list[dict], list[dict], dict]:
        """
        Validate a list of records.
        Returns (valid_records, rejected_records, stats).
        Valid records may have quality_flag = OK or SUSPECT.
        """
        valid, rejected = [], []
        stats = {
            "total": len(records),
            "valid": 0,
            "suspect": 0,
            "rejected": 0,
            "field_errors": {},
        }

        for record in records:
            result = self.validate(record)
            result.record["quality_flag"] = result.quality_flag

            if result.is_valid:
                valid.append(result.record)
                if result.quality_flag == "SUSPECT":
                    stats["suspect"] += 1
                else:
                    stats["valid"] += 1
            else:
                rejected.append(result.record)
                stats["rejected"] += 1
                for err in result.errors:
                    stats["field_errors"].setdefault(err.field, 0)
                    stats["field_errors"][err.field] += 1

        return valid, rejected, stats
