# BlastBox Omega — Demo Solution

This folder holds the **portable Copilot Studio solution** behind the BlastBox Omega
demo: the two solution zips, their unpacked source, the connector code, and the skill
bundles.

## To deploy, use `deploy/`

Don't stand this up by hand. The repo ships a single cross-platform script that does the
whole thing: imports both solutions, deploys every MCP connector's inline code, publishes
customizations, creates the no-auth connections, and publishes the agents, then prints the
one manual UI step that has no API (re-attaching the connection-bound tools).

```bash
pac auth create                   # once: sign pac in to the target tenant
node deploy/deploy.mjs            # guided: pick profile, pick env, deploy
node deploy/deploy.mjs --help     # all options
```

See [`deploy/README.md`](../../deploy/README.md) for the full walkthrough, requirements, and the manual
re-attach table.

## What's in this folder

| File / folder | What it is |
| --- | --- |
| `BlastBoxConnectors_1_0_0_1.zip` | The **connectors** solution (5 inline MCP servers). Imports as unique name `BlastBoxConnectors`. |
| `BlastBoxAgents_1_0_0_1.zip` | The **agents** solution (5 agents + Python skills). Imports as unique name `BlastBoxDeploy`. |
| `connectors/<slug>/` | Each MCP connector's `apiDefinition.json`, `apiProperties.json`, and inline `script.csx` (what the script deploys via `pac connector update`). |
| `skills/` | The Python skill bundles that ride in on the agents solution (reference copies). |
| `src/` | The **unpacked** source of both solutions (`pac solution unpack`), for inspection/diffing. Not imported directly. |

### Connectors (5 inline MCP servers — custom code, no external hosting)

| Connector | Slug | Schema name |
| --- | --- | --- |
| Curb Pickup MCP | `curb-delivery-mcp` | `cat_curb-20pickup-20mcp` |
| Membership MCP v2 | `membership-mcp-v2` | `cat_membership-20mcp-20v2` |
| Order Management MCP | `order-management-mcp` | `new_order-20management-20mcp` |
| Policy RAG MCP v2 | `policy-rag-mcp-v2` | `new_policy-20rag-20mcp-20v2` |
| Warehouse MCP | `warehouse-mcp` | `new_warehouse-20mcp` |

### Agents (5)

| Agent | Role | Tools / connected agents |
| --- | --- | --- |
| **Store Associate Assistant** | Parent — **flagship** (Block Party Trade-Up) | Order Management MCP + Membership MCP v2; connected: Store Policy, Inventory & Fulfillment; skills: prorated-refund-calculator, points-reconciliation, slip-pdf-generator |
| **Returns & Service Assistant** | Parent — **self-serve** (Card Reissue) | Membership MCP v2; connected: Store Policy; skills: card-reissue, membership-card-png |
| **Curb Pickup Assistant** | Parent — **customer pickup** (Weather-aware Curb Pickup) | Curb Pickup MCP + MSN Weather; connected: Store Associate; skills: staging-window-calculator, curbside-slip-pdf |
| **Store Policy Agent** | Connected child | Policy RAG MCP v2 |
| **Inventory & Fulfillment Agent** | Connected child | Warehouse MCP |

## Prerequisites

- A Power Platform environment with **Dataverse** and **Copilot Studio** enabled, and the
  **new Copilot Studio experience** turned on. A **First Release / Early Release**
  environment is strongly preferred.
- Permission to import solutions and create connections in that environment.

## Validate — the three scenarios

After deploying (and doing the one re-attach step the script prints), open each parent
agent in **Preview** and run the scripted transcripts. Use the activity map to confirm
that every expected MCP tool, connector action, connected agent, and Python skill fires.

**Self-Serve Card Reissue** (Returns & Service Assistant) — member `MEGA-BLAST-1024`.
Expect: `get_membership` → identity check → `reissue_card` → `membership-card-png` →
`blastpass_card.png`. Prompts:
`sample/archive/store-solution/evals/self-serve-card-reissue.md`.

**Block Party Trade-Up** (Store Associate Assistant) — member `MEGA-BLAST-1024`. Expect
`$76.66` / `$100.00` / `$23.34`, the three MEGA exclusives, and a generated PDF slip.
Prompts: `sample/archive/store-solution/evals/flagship-block-party-trade-up-runbook.md`.

**Weather-aware Curb Pickup** (Curb Pickup Assistant) — order `ORD-10502`, location
`Pixel Heights, WA`, member `MEGA-BLAST-1024`. Expect a verified order and tier, live
weather relevant to the ETA, deterministic staging, a confirmed bay assignment, and an
optional barcode PDF delivery note. Exact weather, times, and bay vary with live
conditions and current occupancy. Prompts:
`https://microsoft.github.io/new-copilot-studio-tech-guide/scenarios/curb-pickup-assistant`.

## Notes

- All data is mock; serials, prices, and confirmation numbers are illustrative.
- The Python skills ride in on the agents solution and register on publish; no manual
  skill upload is needed.
- `src/` is the `pac solution unpack` output of the two zips — use it to diff or inspect
  the connector code and agent definitions; you do **not** import `src/` directly.
