# package-trim — test matrix (behavior × backend)

Backends: `build` = uv/pytest/just toolchain run; `static` = file/config scan
(no toolchain execution). No sim/rec/live split — this spec has no runtime
service behavior.

| Behavior                                      | AC     | Backend           |
| --------------------------------------------- | ------ | ----------------- |
| workspace syncs with exactly 8 members        | AC-001 | build             |
| CI mirror (ruff + pytest) green               | AC-002 | build             |
| layering invariant across member pyprojects   | AC-003 | static/build gate |
| hdp-hitl promoted, history preserved          | AC-004 | build             |
| transport seam Protocol, no httpx in module   | AC-005 | build             |
| commitlint scope-enum matches member set      | AC-006 | static/build gate |
| README/CLAUDE.md reflect 8-member map         | AC-007 | static/build gate |
| Depth markers truthful per member             | AC-008 | static/build gate |
| concept survival: all submodules import       | AC-009 | build             |
| pytest collection collision-free (importlib)  | AC-010 | build             |
| dependency union: zero new runtime deps       | AC-011 | static/build gate |
