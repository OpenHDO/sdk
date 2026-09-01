#include <openhdo/sdk/model.hpp>

int main() {
    const openhdo::sdk::DeviceDescriptor lamp{
        .id = "lamp.kitchen",
        .name = "Kitchen lamp",
        .roles = {"endpoint", "actuator"},
        .capabilities = {{.id = "power", .version = "1", .commands = {"set"}}},
    };
    if (!lamp.valid() || !lamp.has_role("actuator") || lamp.has_role("display")) {
        return 1;
    }

    const openhdo::sdk::DeviceDescriptor panel{
        .id = "panel.wall",
        .name = "Wall panel",
        .roles = {"controller", "display"},
        .capabilities = {{.id = "dashboard.render", .version = "1", .commands = {"show"}}},
    };
    if (!panel.valid() || !panel.has_role("controller") || !panel.has_role("display")) {
        return 1;
    }
    return 0;
}
