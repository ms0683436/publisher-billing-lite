from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NotFoundError(Exception):
    resource: str
    identifier: str | int

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.resource} not found: {self.identifier}"
