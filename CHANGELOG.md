# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added

- `aks_automation` Python package: typed `AKSManager` wrapping the Azure SDK
  (create, show, list, delete, scale, upgrade, add node pool, credentials).
- `aks` Click CLI with `create`, `delete`, `list`, `show`, `scale`, `upgrade`,
  and `credentials` subcommands.
- `pydantic-settings` configuration and centralised logging.
- Terraform root module with `network` and `aks` sub-modules plus `dev`/`prod`
  environments (azurerm provider, system-assigned identity, VNet/subnet).
- CI pipeline (lint, test matrix, Terraform validate), pre-commit hooks,
  issue/PR templates, CODEOWNERS, and Dependabot.
- Slim CLI Dockerfile, documentation, and open-source project files.
