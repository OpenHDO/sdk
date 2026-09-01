#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <type_traits>
#include <variant>
#include <vector>

namespace openhdo::sdk {

inline constexpr int light_v1 = 1;

namespace roles {
inline constexpr std::string_view physical_device = "physical_device";
inline constexpr std::string_view controller = "controller";
inline constexpr std::string_view display = "display";
inline constexpr std::string_view wall_panel = "wall-panel";
}  // namespace roles

// Roles are extensible strings so a new kind of device does not require a
// protocol-breaking SDK release. A resource may have multiple roles.
struct Capability {
    std::string id;
    std::string version;
    std::vector<std::string> commands;

    [[nodiscard]] bool valid() const noexcept {
        return !id.empty() && !version.empty();
    }
};

struct DeviceDescriptor {
    std::string id;
    std::string name;
    std::vector<std::string> roles;
    std::vector<Capability> capabilities;

    [[nodiscard]] bool valid() const noexcept {
        if (id.empty() || name.empty() || roles.empty()) {
            return false;
        }
        for (const auto& role : roles) {
            if (role.empty()) {
                return false;
            }
        }
        for (const auto& capability : capabilities) {
            if (!capability.valid()) {
                return false;
            }
        }
        return true;
    }

    [[nodiscard]] bool has_role(const std::string_view role) const noexcept {
        for (const auto& candidate : roles) {
            if (candidate == role) {
                return true;
            }
        }
        return false;
    }

    [[nodiscard]] bool is_physical_device() const noexcept {
        return has_role(roles::physical_device) ||
               (has_role("endpoint") && has_role("actuator"));
    }

    [[nodiscard]] bool is_light_controller() const noexcept {
        return has_role(roles::controller) &&
               (has_role(roles::display) || has_role(roles::wall_panel));
    }
};

namespace light {

namespace detail {
inline bool valid_identifier(const std::string& value) noexcept {
    if (value.size() < 2 || value.size() > 64 || value.front() < 'a' ||
        value.front() > 'z') {
        return false;
    }
    for (const char character : value) {
        if (!((character >= 'a' && character <= 'z') ||
              (character >= '0' && character <= '9') || character == '.' ||
              character == '_' || character == '-')) {
            return false;
        }
    }
    return true;
}

inline bool valid_type(const std::string& value) noexcept {
    if (value.empty() || value.size() > 64 || value.front() < 'a' ||
        value.front() > 'z') {
        return false;
    }
    for (const char character : value) {
        if (!((character >= 'a' && character <= 'z') ||
              (character >= '0' && character <= '9') || character == '.' ||
              character == '_' || character == '-')) {
            return false;
        }
    }
    return true;
}

inline bool valid_uuid(const std::string& value) noexcept {
    if (value.size() != 36) {
        return false;
    }
    for (std::size_t i = 0; i < value.size(); ++i) {
        const char character = value[i];
        if (i == 8 || i == 13 || i == 18 || i == 23) {
            if (character != '-') {
                return false;
            }
            continue;
        }
        const bool hex = (character >= '0' && character <= '9') ||
                         (character >= 'a' && character <= 'f') ||
                         (character >= 'A' && character <= 'F');
        if (!hex) {
            return false;
        }
    }
    return true;
}

inline bool valid_timestamp(const std::string& value) noexcept {
    if (value.size() < 20 || value[4] != '-' || value[7] != '-' ||
        (value[10] != 'T' && value[10] != 't') || value[13] != ':' ||
        value[16] != ':') {
        return false;
    }
    for (const std::size_t index : {0u, 1u, 2u, 3u, 5u, 6u, 8u, 9u, 11u,
                                    12u, 14u, 15u}) {
        if (value[index] < '0' || value[index] > '9') {
            return false;
        }
    }
    return value.back() == 'Z' || value.back() == 'z';
}

inline bool valid_source(const std::string& value) noexcept {
    return !value.empty() && value.size() <= 128;
}
}  // namespace detail

struct RgbColor {
    int r = 0;
    int g = 0;
    int b = 0;

    [[nodiscard]] bool valid() const noexcept {
        return r >= 0 && r <= 255 && g >= 0 && g <= 255 && b >= 0 && b <= 255;
    }
};

struct LightState {
    std::string light_id;
    bool power = false;
    int brightness = 0;
    RgbColor rgb_color;
    std::int64_t state_revision = 0;

    [[nodiscard]] bool valid() const noexcept {
        return detail::valid_identifier(light_id) && brightness >= 0 &&
               brightness <= 255 && rgb_color.valid() && state_revision >= 0;
    }
};

struct PowerCommand {
    std::string light_id;
    std::string command_id;
    std::string idempotency_key;
    bool power = false;

    [[nodiscard]] bool valid() const noexcept {
        return detail::valid_identifier(light_id) &&
               detail::valid_uuid(command_id) && !idempotency_key.empty() &&
               idempotency_key.size() <= 128;
    }
};

struct BrightnessCommand {
    std::string light_id;
    std::string command_id;
    std::string idempotency_key;
    int brightness = 0;

    [[nodiscard]] bool valid() const noexcept {
        return detail::valid_identifier(light_id) &&
               detail::valid_uuid(command_id) && !idempotency_key.empty() &&
               idempotency_key.size() <= 128 && brightness >= 0 &&
               brightness <= 255;
    }
};

struct RgbColorCommand {
    std::string light_id;
    std::string command_id;
    std::string idempotency_key;
    RgbColor rgb_color;

    [[nodiscard]] bool valid() const noexcept {
        return detail::valid_identifier(light_id) &&
               detail::valid_uuid(command_id) && !idempotency_key.empty() &&
               idempotency_key.size() <= 128 && rgb_color.valid();
    }
};

using Command = std::variant<PowerCommand, BrightnessCommand, RgbColorCommand>;

struct Envelope {
    int v = light_v1;
    std::string id;
    std::string type;
    std::string ts;
    std::string source;
    std::optional<std::string> correlation_id;

    [[nodiscard]] bool valid() const noexcept {
        return v == light_v1 && detail::valid_uuid(id) &&
               detail::valid_type(type) && detail::valid_timestamp(ts) &&
               detail::valid_source(source) &&
               (!correlation_id || detail::valid_uuid(*correlation_id));
    }
};

struct CommandMessage {
    Envelope envelope;
    Command payload;

    [[nodiscard]] bool valid() const noexcept {
        if (!envelope.valid() || !envelope.correlation_id) {
            return false;
        }
        return std::visit(
            [this](const auto& command) {
                using T = std::decay_t<decltype(command)>;
                if (!command.valid()) {
                    return false;
                }
                if constexpr (std::is_same_v<T, PowerCommand>) {
                    return envelope.type == "light.command.power";
                } else if constexpr (std::is_same_v<T, BrightnessCommand>) {
                    return envelope.type == "light.command.brightness";
                }
                return envelope.type == "light.command.rgb_color";
            },
            payload);
    }
};

struct ReportedStateMessage {
    Envelope envelope;
    LightState payload;

    [[nodiscard]] bool valid() const noexcept {
        return envelope.valid() && !envelope.correlation_id &&
               envelope.type == "light.state.reported" && payload.valid();
    }
};

struct ChangedState {
    LightState state;
    std::string command_id;
    std::string idempotency_key;

    [[nodiscard]] bool valid() const noexcept {
        return state.valid() && detail::valid_uuid(command_id) &&
               !idempotency_key.empty() && idempotency_key.size() <= 128;
    }
};

struct ChangedStateMessage {
    Envelope envelope;
    ChangedState payload;

    [[nodiscard]] bool valid() const noexcept {
        return envelope.valid() && envelope.correlation_id &&
               envelope.type == "light.state.changed" && payload.valid();
    }
};

}  // namespace light

}  // namespace openhdo::sdk
