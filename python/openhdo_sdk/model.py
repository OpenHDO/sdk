"""Small, dependency-free SDK domain model.

Devices and controllers share one descriptor because a real resource can have
multiple roles. Transport and server persistence stay outside this package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any, Mapping
from uuid import UUID, uuid4

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9._-]{1,63}$")
_TYPE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")

LIGHT_V1 = 1
PHYSICAL_DEVICE_ROLE = "physical_device"
CONTROLLER_ROLE = "controller"
DISPLAY_ROLE = "display"
WALL_PANEL_ROLE = "wall-panel"


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

    def is_physical_device(self) -> bool:
        return PHYSICAL_DEVICE_ROLE in self.roles or {"endpoint", "actuator"} <= self.roles

    def is_light_controller(self) -> bool:
        return CONTROLLER_ROLE in self.roles and bool(
            {DISPLAY_ROLE, WALL_PANEL_ROLE} & self.roles
        )

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


def _check_light_id(light_id: str) -> None:
    if not isinstance(light_id, str) or not _IDENTIFIER.fullmatch(light_id):
        raise ModelError("light_id must be a lowercase identifier")


def _check_uuid(value: UUID, field_name: str) -> None:
    if not isinstance(value, UUID):
        raise ModelError(f"{field_name} must be a UUID")


def _check_idempotency_key(value: str) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ModelError("idempotency_key must contain 1 to 128 characters")


@dataclass(frozen=True, slots=True)
class RgbColor:
    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        if any(
            not isinstance(channel, int)
            or isinstance(channel, bool)
            or not 0 <= channel <= 255
            for channel in (self.r, self.g, self.b)
        ):
            raise ModelError("rgb_color channels must be integers from 0 to 255")

    def to_dict(self) -> dict[str, int]:
        return {"r": self.r, "g": self.g, "b": self.b}


@dataclass(frozen=True, slots=True)
class LightState:
    light_id: str
    power: bool
    brightness: int
    rgb_color: RgbColor
    state_revision: int

    def __post_init__(self) -> None:
        _check_light_id(self.light_id)
        if not isinstance(self.power, bool):
            raise ModelError("power must be a boolean")
        if (
            not isinstance(self.brightness, int)
            or isinstance(self.brightness, bool)
            or not 0 <= self.brightness <= 255
        ):
            raise ModelError("brightness must be an integer from 0 to 255")
        if not isinstance(self.rgb_color, RgbColor):
            raise ModelError("rgb_color must be an RgbColor")
        if (
            not isinstance(self.state_revision, int)
            or isinstance(self.state_revision, bool)
            or self.state_revision < 0
        ):
            raise ModelError("state_revision must be a non-negative integer")

    def to_dict(self) -> dict[str, object]:
        return {
            "light_id": self.light_id,
            "power": self.power,
            "brightness": self.brightness,
            "rgb_color": self.rgb_color.to_dict(),
            "state_revision": self.state_revision,
        }


@dataclass(frozen=True, slots=True)
class CommandIdentity:
    light_id: str
    command_id: UUID
    idempotency_key: str

    def __post_init__(self) -> None:
        _check_light_id(self.light_id)
        _check_uuid(self.command_id, "command_id")
        _check_idempotency_key(self.idempotency_key)

    def _to_dict(self) -> dict[str, object]:
        return {
            "light_id": self.light_id,
            "command_id": str(self.command_id),
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True, slots=True)
class PowerCommand(CommandIdentity):
    power: bool

    def __post_init__(self) -> None:
        CommandIdentity.__post_init__(self)
        if not isinstance(self.power, bool):
            raise ModelError("power must be a boolean")

    def to_dict(self) -> dict[str, object]:
        return {**self._to_dict(), "power": self.power}

    @property
    def type(self) -> str:
        return "light.command.power"


@dataclass(frozen=True, slots=True)
class BrightnessCommand(CommandIdentity):
    brightness: int

    def __post_init__(self) -> None:
        CommandIdentity.__post_init__(self)
        if (
            not isinstance(self.brightness, int)
            or isinstance(self.brightness, bool)
            or not 0 <= self.brightness <= 255
        ):
            raise ModelError("brightness must be an integer from 0 to 255")

    def to_dict(self) -> dict[str, object]:
        return {**self._to_dict(), "brightness": self.brightness}

    @property
    def type(self) -> str:
        return "light.command.brightness"


@dataclass(frozen=True, slots=True)
class RgbColorCommand(CommandIdentity):
    rgb_color: RgbColor

    def __post_init__(self) -> None:
        CommandIdentity.__post_init__(self)
        if not isinstance(self.rgb_color, RgbColor):
            raise ModelError("rgb_color must be an RgbColor")

    def to_dict(self) -> dict[str, object]:
        return {**self._to_dict(), "rgb_color": self.rgb_color.to_dict()}

    @property
    def type(self) -> str:
        return "light.command.rgb_color"


@dataclass(frozen=True, slots=True)
class Envelope:
    id: UUID
    type: str
    ts: str
    source: str
    correlation_id: UUID | None = None
    v: int = LIGHT_V1

    def __post_init__(self) -> None:
        _check_uuid(self.id, "id")
        if not isinstance(self.v, int) or self.v != LIGHT_V1:
            raise ModelError("v must be 1")
        if not isinstance(self.type, str) or not _TYPE.fullmatch(self.type):
            raise ModelError("type must be a lowercase identifier")
        if not isinstance(self.ts, str):
            raise ModelError("ts must be an ISO-8601 date-time")
        try:
            parsed = datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
        except ValueError as error:
            raise ModelError("ts must be an ISO-8601 date-time") from error
        if parsed.tzinfo is None:
            raise ModelError("ts must include a timezone")
        if not isinstance(self.source, str) or not 1 <= len(self.source) <= 128:
            raise ModelError("source must contain 1 to 128 characters")
        if self.correlation_id is not None:
            _check_uuid(self.correlation_id, "correlation_id")

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "v": self.v,
            "id": str(self.id),
            "type": self.type,
            "ts": self.ts,
            "source": self.source,
        }
        if self.correlation_id is not None:
            result["correlation_id"] = str(self.correlation_id)
        return result


CommandPayload = PowerCommand | BrightnessCommand | RgbColorCommand


@dataclass(frozen=True, slots=True)
class LightCommandMessage:
    envelope: Envelope
    payload: CommandPayload

    def __post_init__(self) -> None:
        if self.envelope.correlation_id is None:
            raise ModelError("light commands require correlation_id")
        if not isinstance(self.payload, (PowerCommand, BrightnessCommand, RgbColorCommand)):
            raise ModelError("payload must be a Light v1 command")
        if self.envelope.type != self.payload.type:
            raise ModelError("envelope type does not match command payload")

    def to_dict(self) -> dict[str, object]:
        return {**self.envelope.to_dict(), "payload": self.payload.to_dict()}


@dataclass(frozen=True, slots=True)
class LightStateReportedMessage:
    envelope: Envelope
    payload: LightState

    def __post_init__(self) -> None:
        if self.envelope.correlation_id is not None or self.envelope.type != "light.state.reported":
            raise ModelError("reported state has no correlation_id and uses its fixed type")
        if not isinstance(self.payload, LightState):
            raise ModelError("payload must be a LightState")

    def to_dict(self) -> dict[str, object]:
        return {**self.envelope.to_dict(), "payload": self.payload.to_dict()}


@dataclass(frozen=True, slots=True)
class LightStateChangedPayload:
    state: LightState
    command_id: UUID
    idempotency_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, LightState):
            raise ModelError("state must be a LightState")
        _check_uuid(self.command_id, "command_id")
        _check_idempotency_key(self.idempotency_key)

    def to_dict(self) -> dict[str, object]:
        return {
            **self.state.to_dict(),
            "command_id": str(self.command_id),
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True, slots=True)
class LightStateChangedMessage:
    envelope: Envelope
    payload: LightStateChangedPayload

    def __post_init__(self) -> None:
        if self.envelope.correlation_id is None or self.envelope.type != "light.state.changed":
            raise ModelError("changed state requires correlation_id and its fixed type")
        if not isinstance(self.payload, LightStateChangedPayload):
            raise ModelError("payload must be a LightStateChangedPayload")

    def to_dict(self) -> dict[str, object]:
        return {**self.envelope.to_dict(), "payload": self.payload.to_dict()}
