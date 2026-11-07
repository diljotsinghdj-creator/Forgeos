# ForgeOS

Native Android development and build environment designed to compile, test, package, sign and install Android applications without relying on Termux.

## Apps

| Module | App ID | What it is |
|---|---|---|
| `app` | `com.forgeos.app` | **ForgeOS v0.4** – import a project ZIP, run an offline inspection (build readiness, dependencies, supply-chain scan, SHA-256 manifest), and submit remote builds as durable missions. |
| `apex` | `com.apex.command` | **APEX v0.1** – Mission Control shell with a persisted, recoverable mission lifecycle (planning → running → recovery → verification). |

## Build

`.github/workflows/build-forgeos.yml` lints, tests and builds both modules on every push and PR, and uploads `ForgeOS-debug-apk` and `APEX-debug-apk` artifacts.

Projects imported into ForgeOS are built by `.github/workflows/remote-project-build.yml`: the app uploads the project ZIP to the `build-requests` branch (creating it if missing) and dispatches that workflow, which publishes the APK as an artifact.
