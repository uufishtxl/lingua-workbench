# Triage Labels

## Canonical Roles

| Role | Label | Description |
|------|-------|-------------|
| Needs triage | `needs-triage` | Maintainer needs to evaluate |
| Needs info | `needs-info` | Waiting on reporter |
| Ready for agent | `ready-for-agent` | Fully specified, AFK-ready |
| Ready for human | `ready-for-human` | Needs human implementation |
| Won't fix | `wontfix` | Will not be actioned |

## Usage

When processing incoming issues, the triage skill will:

1. Add `needs-triage` label to new issues
2. Move to `needs-info` if more information is required
3. Move to `ready-for-agent` when fully specified
4. Move to `ready-for-human` when human implementation is needed
5. Move to `wontfix` if the issue will not be addressed
