#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace openhdo::sdk {

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
};

}  // namespace openhdo::sdk
