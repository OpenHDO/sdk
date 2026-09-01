"""Small, dependency-free SDK domain model.

Devices and controllers share one descriptor because a real resource can have
multiple roles. Transport and server persistence stay outside this package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping
from uuid import UUID, uuid4

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9._-]{1,63}$")


class ModelError(ValueError):
    """Raised when an SDK model cannot be represented by the contract."""


@dataclass(frozen=True, slots=True)
class Capability:
    id: str
    version: str
    commands: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _IDENTIFIER.fullmatch(self.id):
            raise ModelError("capability id must be a lowercase identifier")
        if not isinstance(self.version, str) or not self.version:
            raise ModelError("capability version must not be empty")
        if not isinstance(self.commands, tuple) or any(
            not isinstance(command, str) or not _IDENTIFIER.fullmatch(command)
            for command in self.commands
        ):
            raise ModelError("commands must be lowercase identifiers")

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "version": self.version, "commands": list(self.commands)}


@dataclass(frozen=True, slots=True)
class DeviceDescriptor:
    id: str
    name: str
    roles: frozenset[str]
    capabilities: tuple[Capability, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _IDENTIFIER.fullmatch(self.id):
            raise ModelError("device id must be a lowercase identifier")
        if not isinstance(self.name, str) or not self.name or len(self.name) > 128:
            raise ModelError("device name must contain 1 to 128 characters")
        if not isinstance(self.roles, frozenset) or not self.roles or any(
            not isinstance(role, str) or not _IDENTIFIER.fullmatch(role) for role in self.roles
        ):
            raise ModelError("roles must be a non-empty set of lowercase identifiers")
        if not isinstance(self.capabilities, tuple):
            raise ModelError("capabilities must be a tuple")
        capability_ids = [capability.id for capability in self.capabilities]
        if len(set(capability_ids)) != len(capability_ids):
            raise ModelError("capability ids must be unique")
        if not isinstance(self.metadata, Mapping):
            raise ModelError("metadata must be an object")

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "roles": sorted(self.roles),
            "capabilities": [capability.to_dict() for capability in self.capabilities],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CommandRequest:
    device_id: str
    capability: str
    command: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.device_id, "device_id"),
            (self.capability, "capability"),
            (self.command, "command"),
        ):
            if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
                raise ModelError(f"{field_name} must be a lowercase identifier")
        if not isinstance(self.arguments, Mapping):
            raise ModelError("arguments must be an object")
        if not isinstance(self.correlation_id, UUID):
            raise ModelError("correlation_id must be a UUID")

    def to_dict(self) -> dict[str, object]:
        return {
            "device_id": self.device_id,
            "capability": self.capability,
            "command": self.command,
            "arguments": dict(self.arguments),
            "correlation_id": str(self.correlation_id),
        }
