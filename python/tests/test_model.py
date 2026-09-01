import unittest
from uuid import UUID, uuid4

from openhdo_sdk import (
    BrightnessCommand,
    Capability,
    CommandRequest,
    DeviceDescriptor,
    Envelope,
    LightCommandMessage,
    LightState,
    LightStateChangedMessage,
    LightStateChangedPayload,
    LightStateReportedMessage,
    PowerCommand,
    RgbColor,
    RgbColorCommand,
)
from openhdo_sdk.model import ModelError


class ModelTests(unittest.TestCase):
    def test_supports_devices_and_controllers(self) -> None:
        lamp = DeviceDescriptor(
            "lamp.kitchen",
            "Kitchen lamp",
            frozenset({"endpoint", "actuator"}),
            (Capability("power", "1", ("set",)),),
        )
        panel = DeviceDescriptor(
            "panel.wall",
            "Wall panel",
            frozenset({"controller", "display"}),
            (Capability("dashboard.render", "1", ("show",)),),
        )

        self.assertTrue(lamp.has_role("actuator"))
        self.assertTrue(lamp.is_physical_device())
        self.assertTrue(panel.has_role("controller"))
        self.assertTrue(panel.is_light_controller())
        self.assertEqual(panel.to_dict()["roles"], ["controller", "display"])

    def test_resource_can_have_multiple_roles(self) -> None:
        hybrid = DeviceDescriptor("tablet.wall", "Wall tablet", frozenset({"controller", "display", "sensor"}))
        self.assertTrue(hybrid.has_role("controller"))
        self.assertTrue(hybrid.has_role("sensor"))

    def test_command_request_has_correlation_id(self) -> None:
        request = CommandRequest("lamp.kitchen", "power", "set", {"value": True})
        self.assertIsInstance(request.to_dict()["correlation_id"], str)
        UUID(request.to_dict()["correlation_id"])

    def test_rejects_duplicate_capabilities(self) -> None:
        with self.assertRaises(ModelError):
            DeviceDescriptor(
                "lamp.kitchen",
                "Kitchen lamp",
                frozenset({"endpoint"}),
                (Capability("power", "1"), Capability("power", "1")),
            )

    def test_light_v1_commands_and_state_match_contract_shapes(self) -> None:
        command_id = uuid4()
        correlation_id = uuid4()
        command = PowerCommand("living-room-lamp", command_id, "power-001", True)
        message = LightCommandMessage(
            Envelope(uuid4(), command.type, "2026-01-01T00:00:00Z", "panel.wall", correlation_id),
            command,
        )
        self.assertEqual(message.to_dict()["payload"], {
            "light_id": "living-room-lamp",
            "command_id": str(command_id),
            "idempotency_key": "power-001",
            "power": True,
        })

        state = LightState("living-room-lamp", True, 0, RgbColor(0, 96, 255), 42)
        reported = LightStateReportedMessage(
            Envelope(uuid4(), "light.state.reported", "2026-01-01T00:00:01Z", "linker.example"),
            state,
        )
        changed = LightStateChangedMessage(
            Envelope(uuid4(), "light.state.changed", "2026-01-01T00:00:02Z", "openhdo-server", correlation_id),
            LightStateChangedPayload(state, command_id, "power-001"),
        )
        self.assertEqual(reported.to_dict()["payload"]["brightness"], 0)
        self.assertEqual(changed.to_dict()["payload"]["command_id"], str(command_id))

    def test_light_v1_rejects_out_of_range_values(self) -> None:
        with self.assertRaises(ModelError):
            RgbColor(256, 0, 0)
        with self.assertRaises(ModelError):
            BrightnessCommand("living-room-lamp", uuid4(), "brightness-001", -1)
        with self.assertRaises(ModelError):
            RgbColorCommand("living-room-lamp", uuid4(), "rgb-001", (255, 0, 0))

    def test_wall_panel_role_is_a_controller(self) -> None:
        panel = DeviceDescriptor(
            "panel.wall",
            "Wall panel",
            frozenset({"controller", "wall-panel"}),
        )
        self.assertTrue(panel.is_light_controller())


if __name__ == "__main__":
    unittest.main()
