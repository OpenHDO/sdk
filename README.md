# OpenHDO SDK

The SDK repository provides language-neutral contracts and small client
libraries for servers, Linkers, agents, plugins, and applications.

## Direction

- C++ first for native runtime and plugin development;
- Python as a dependency-light option for clients and Linker drivers;
- one extensible resource model for physical devices, sensors, actuators,
  controllers, displays, and hybrid devices;
- versioned JSON Schema contracts at every process boundary;
- no dependency on server internals or SQLite tables.

The current package includes transport-free C++20 and Python models. A lamp is
an `endpoint`/`actuator`; a wall panel can be a `controller`/`display`; one
resource may have multiple roles. `CommandRequest` carries a correlation ID so
the transport can use request/reply semantics without coupling the SDK to a
specific broker or socket library.

## Status

The SDK is intentionally small. Protocol schemas remain normative in the
[server](https://github.com/OpenHDO/server/tree/master/contracts) repository;
this repository derives reusable types and must not silently fork them.

## Verify

```bash
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
cd python
python -m unittest discover -s tests -v
```

See the [project architecture](https://github.com/OpenHDO/about/blob/main/ARCHITECTURE.md).
