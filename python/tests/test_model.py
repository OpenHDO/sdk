import unittest
from uuid import UUID

from openhdo_sdk import Capability, CommandRequest, DeviceDescriptor
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
        self.assertTrue(panel.has_role("controller"))
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


if __name__ == "__main__":
    unittest.main()
