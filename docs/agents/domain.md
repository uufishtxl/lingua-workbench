# Domain Docs

## Layout

Single-context layout with `CONTEXT.md` and `docs/adr/` at repo root.

## Files

- `CONTEXT.md` - Project domain language and context
- `docs/adr/` - Architectural Decision Records

## Usage

- Skills like `improve-codebase-architecture`, `diagnosing-bugs`, and `tdd` read `CONTEXT.md` to learn the project's domain language
- `docs/adr/` contains past architectural decisions for reference

## Creating Context

When creating `CONTEXT.md`, include:

1. Project overview and purpose
2. Key domain terms and definitions
3. Technical stack and dependencies
4. Architecture overview
5. Coding conventions and standards

## Creating ADRs

When creating ADRs in `docs/adr/`, follow the format:

1. Title
2. Status (proposed, accepted, deprecated, superseded)
3. Context
4. Decision
5. Consequences
