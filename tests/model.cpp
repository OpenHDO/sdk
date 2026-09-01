#include <openhdo/sdk/model.hpp>

int main() {
    const openhdo::sdk::DeviceDescriptor lamp{
        .id = "lamp.kitchen",
        .name = "Kitchen lamp",
        .roles = {"endpoint", "actuator"},
        .capabilities = {{.id = "power", .version = "1", .commands = {"set"}}},
    };
    if (!lamp.valid() || !lamp.has_role("actuator") || !lamp.is_physical_device() ||
        lamp.has_role("display")) {
        return 1;
    }

    const openhdo::sdk::DeviceDescriptor panel{
        .id = "panel.wall",
        .name = "Wall panel",
        .roles = {"controller", "display"},
        .capabilities = {{.id = "dashboard.render", .version = "1", .commands = {"show"}}},
    };
    if (!panel.valid() || !panel.has_role("controller") || !panel.has_role("display") ||
        !panel.is_light_controller()) {
        return 1;
    }

    const openhdo::sdk::light::RgbColor orange{255, 96, 32};
    const openhdo::sdk::light::LightState state{
        .light_id = "living-room-lamp",
        .power = true,
        .brightness = 255,
        .rgb_color = orange,
        .state_revision = 41,
    };
    if (!state.valid() || openhdo::sdk::light::RgbColor{256, 0, 0}.valid()) {
        return 1;
    }

    const openhdo::sdk::light::PowerCommand power{
        .light_id = "living-room-lamp",
        .command_id = "00000000-0000-4000-8000-000000000103",
        .idempotency_key = "living-room-lamp-power-001",
        .power = true,
    };
    const openhdo::sdk::light::CommandMessage command{
        .envelope = {
            .v = 1,
            .id = "00000000-0000-4000-8000-000000000101",
            .type = "light.command.power",
            .ts = "2026-01-01T00:00:00Z",
            .source = "panel.wall",
            .correlation_id = "00000000-0000-4000-8000-000000000102",
        },
        .payload = power,
    };
    if (!command.valid()) {
        return 1;
    }

    const openhdo::sdk::light::ReportedStateMessage reported{
        .envelope = {
            .v = 1,
            .id = "00000000-0000-4000-8000-000000000110",
            .type = "light.state.reported",
            .ts = "2026-01-01T00:00:03Z",
            .source = "linker.example",
        },
        .payload = state,
    };
    if (!reported.valid()) {
        return 1;
    }
    return 0;
}
