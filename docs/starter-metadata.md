# Starter Metadata Ownership

These files are treated as starter-owned metadata and are rewritten by `src/metadata.js`
when the project is generated. They are the complete list — if a file is not here, the
generator will not touch it.

## Backend Metadata

- `backend/go.mod`
  - owns the backend module path
- `backend/.golangci.yml`
  - owns `gofumpt.module-path` and `goimports.local-prefixes`, which decide how the
    project's own imports are grouped
- `backend/Makefile`
  - owns the default backend binary name
- `backend/cmd/main.go`
  - owns the CLI `Use` value and backend short description
- `backend/conf/conf.go`
  - owns the default backend app name and environment variable prefix
- `backend/etc/config.dev.yaml`
  - owns the development default app name
- `backend/etc/config.prod.yaml`
  - owns the production default app name

## Frontend Metadata

- `frontend/package.json`
  - owns the frontend package name
- `frontend/package-lock.json`
  - mirrors the frontend package name used by package managers
- `frontend/index.html`
  - owns the browser title shown for the starter app

## OpenSpec Metadata

- `openspec/config.yaml`
  - is fully rewritten by `src/openspec.js` with the project name, module path and tech
    stack; the template copy is a placeholder

## Replacement Policy

The initialization workflow is intentionally narrow:

- it updates repository identity and metadata
- it does not rename the `sample` feature into a user-specific business domain
- it does not generate optional stacks such as databases, auth providers, or CI variants

That scope keeps the starter deterministic and easy to verify.
