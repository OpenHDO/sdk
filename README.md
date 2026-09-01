# OpenHDO SDK

The SDK repository will provide language-neutral contracts and small client
libraries for servers, Linkers, agents, plugins, and applications.

## Direction

- C++ first for native runtime and plugin development;
- Python as a dependency-light option for clients and Linker drivers;
- versioned JSON Schema contracts at every process boundary;
- no dependency on server internals or SQLite tables.

The current reference Python SDK lives in
[server/python](https://github.com/OpenHDO/server/tree/master/python) until it
needs an independent release cycle.

## Status

Repository scaffold. Extract shared protocol types here when the first
end-to-end server/Linker flow proves which APIs are genuinely reusable.

See the [project architecture](https://github.com/OpenHDO/about/blob/main/ARCHITECTURE.md).
