# BlastBox Omega — repeatable deploy (`deploy/`)

One cross-platform Node script (`deploy.mjs`) that stands up the BlastBox demo in
an **existing** Power Platform environment. It imports the two solutions, deploys
each MCP connector's inline custom code, publishes all customizations, creates the
no-auth MCP connections, publishes the agents, and prints the single manual UI
step that has no API.

Run it from a fresh clone — everything it needs (both solution zips and all
connector code) is in the repo. It does **not** create or delete environments; you
point it at an env you already have.

## Quickest path — one command, no clone

Deploy the sample without cloning anything. This downloads the deploy assets (both
solution zips and all connector code) and starts the same guided deploy:

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/microsoft/new-copilot-studio-tech-guide/sample-first-installer/deploy/install.sh | BLASTBOX_REF=sample-first-installer bash
```

**Windows (PowerShell)**

```powershell
powershell -c "$env:BLASTBOX_REF='sample-first-installer'; irm https://raw.githubusercontent.com/microsoft/new-copilot-studio-tech-guide/sample-first-installer/deploy/install.ps1 | iex"
```

Set the `BLASTBOX_REF` env var to deploy from a branch or tag other than `main`. You
still need the [requirements](#requirements) below — Node 18+, the pac CLI signed in,
and the az CLI.

### Prefer to clone?

Everything the script needs is committed in the repo, so a clone works too:

```bash
node deploy/deploy.mjs            # guided: pick profile, pick env, deploy
node deploy/deploy.mjs --help     # all options
```

The script is cross-OS (Windows, macOS, Linux): it shells out with argument
arrays (no shell string interpolation), resolves paths with `node:path`, and reads
`DOTNET_ROOT` from `$DOTNET_ROOT` or `~/.dotnet`.

## TL;DR — the happy path

1. **Sign pac in to the target tenant** (once):

   ```bash
   pac auth create            # then verify with: pac auth list
   ```

2. **Deploy** (guided — it lists your profiles and envs). Run the no-clone one-liner
   from the [Quickest path](#quickest-path--one-command-no-clone) above, or from a
   clone:

   ```bash
   node deploy/deploy.mjs
   ```

3. **Re-attach the MCP tools** — the one manual UI step (~2 min). The script
   also prints these instructions at the end of the run.

   1. Open **Copilot Studio** (https://copilotstudio.microsoft.com/) in the deployed env.
   2. For **each** agent below: open it, go to **Tools → Add a tool → Model Context
      Protocol (MCP)**, search the connector by name, pick **`<Name> Server`**, select
      the **existing Connected connection** (the picker pre-selects it — do not create a
      new one), **Add**, then **Save and publish**.

      | Agent | MCP server(s) to add |
      | --- | --- |
      | Store Policy Agent | Policy RAG MCP v2 |
      | Inventory & Fulfillment Agent | Warehouse MCP |
      | Returns & Service Assistant | Membership MCP v2 |
      | Store Associate Assistant | Order Management MCP **and** Membership MCP v2 |

   That is 5 attachments total. See [Manual post-install step](#manual-post-install-step-required-2-min)
   for why this can't be scripted.

4. **Validate using the scenarios** at
   https://microsoft.github.io/new-copilot-studio-tech-guide/#scenarios — open
   the matching agent's **Preview** and walk a scenario end to end. Done.

## Requirements

- **Node 18+** (uses global `fetch` and `node:crypto`). No `npm install` needed.
- **pac CLI**, authenticated, with access to the target env. pac needs
  `DOTNET_ROOT` pointing at a .NET runtime; the script defaults to `$DOTNET_ROOT`
  or `~/.dotnet`, or pass `--dotnet-root <path>`.
- **az CLI** installed. You do **not** need to log in first: the script reads the
  tenant from the pac profile you pick and runs `az login --tenant <that tenant>`
  for you if az isn't already signed in to it. az is used for the REST calls pac
  cannot make (BAP no-auth connection creation, and the Dataverse import /
  connector / publish verification calls).

## Options

| Flag | Meaning |
| --- | --- |
| `--env-id <guid>` / `--env-url <url>` | Target env. Omit and the script offers the profile's connected env as the default, or lets you filter the (often huge) env list by a name/url substring. |
| `--profile <n>` | pac auth list index to use. Omit to choose interactively. |
| `--start-at <step>` | Resume at `import`, `connectors`, `connections`, `publish` or `manual`. |
| `--yes` | Do not pause for confirmations (non-interactive / CI). |
| `--dotnet-root <path>` | Set `DOTNET_ROOT` for the pac child processes. |
| `-h`, `--help` | Print usage and exit. |

Every step is idempotent and re-runnable, so if a run dies partway you can re-run
the whole thing or jump back in with `--start-at`.

Unattended into a known env (non-interactive / CI):

```bash
node deploy/deploy.mjs \
  --env-id <env-guid> \
  --env-url https://<org>.crm.dynamics.com/ \
  --yes
```

## What the script does

The demo ships as **two solutions** that import in order:

| # | Solution (zip) | Imports as unique name | Carries |
| --- | --- | --- | --- |
| 1 | `BlastBoxConnectors_1_0_0_1.zip` | `BlastBoxConnectors` | the 4 custom MCP connectors |
| 2 | `BlastBoxAgents_1_0_0_1.zip` | `BlastBoxDeploy` | the 4 agents + their Python skills |

Both zips are committed under `sample/solution/`, and each is also **unpacked**
into `sample/solution/src/<UniqueName>/` so the solution contents are reviewable
and diffable in git.

Run steps:

1. **Import** both solutions in order (`pac solution import`), connectors first so
   the agents' tools resolve against connectors that already exist. The custom-code
   compile routinely exceeds pac's 30-minute client timeout while the **server**
   job keeps running, so success is verified server-side (polling Dataverse), and
   each import is allowed to fully **settle** (polling `importjobs` for
   `completedon`) before the next one starts — otherwise the second import is
   rejected with "a previous Import is still running". Retries with backoff handle
   the EU function-app capacity error.
2. **Connectors:** deploy each MCP connector's inline `.csx` from the bundled files
   in `sample/solution/connectors/<slug>/` (import registers the connectors but does
   **not** compile their code). Each is `pac connector update`-d and verified by
   watching its Dataverse `modifiedon` advance. Then **Publish All Customizations**
   (Dataverse `PublishAllXml`) — this is the step that makes the custom MCP
   connectors appear in the modern "Add a tool, Model Context Protocol" picker.
   Finally a **settle pass** re-deploys + republishes the connector(s) flagged
   `settlePass: true` in the manifest (only the large Warehouse connector, whose
   runtime code binding can go stale after the first deploy).
3. **Connections:** create one no-auth connection per connector via the BAP REST
   API (idempotent — an existing Connected connection is reused). No guid binding is
   needed; `authMode: Maker` resolves any Connected connection for that connector.
4. **Publish:** `PvaPublish` the 4 agents, children before parents.
5. **Manual step:** print the one UI action that has no supported API (below).

`pac connector update` can hang for 30+ minutes on these connectors even when the
server compile succeeds, so it runs in its own process group with a deadline and
the step resolves the moment `modifiedon` advances — it never blocks on a hung pac.

## Manual post-install step (required, ~2 min)

Everything above is automated. The one thing the script cannot do (there is no
supported API for it) is finalise each agent's MCP tool wiring. New-UI MCP
connection references don't survive solution export cleanly, so the sanitized
agents solution ships **without** the MCP tools, and the modern Copilot Studio
canvas only re-creates a working tool binding when a maker re-attaches the MCP
server in the UI. The connectors and Connected connections already exist, so this
is just a few clicks per agent.

The concrete steps and the agent → MCP table are in
[Step 3 of the happy path](#tldr--the-happy-path) above. `deploy.mjs` also prints
them at the end of every run (or run `node deploy/deploy.mjs --start-at manual ...`
to re-print). After re-attaching (5 attachments total), the tools load and both
packaged scenarios work end to end.

## Verify (end-to-end test)

Validate using the scenarios at
https://microsoft.github.io/new-copilot-studio-tech-guide/#scenarios — each one
names the agent to test it with and the exact turns to paste. Both scenarios have
been validated on a fresh env after a clean scripted run, with every MCP tool and
every Python skill firing live (visible in the agent's activity map):

- **Block Party Trade-Up** — open **Store Associate Assistant, Preview** and paste
  the 4 turns from
  `sample/archive/store-solution/evals/flagship-block-party-trade-up-runbook.md`.
  Expect: `$76.66` / `$100.00` / `$23.34`, the three MEGA exclusives, and a
  generated PDF slip. Tools that fire: Store Policy Agent, `get_membership`,
  Inventory & Fulfillment, `get_console_exclusives`, `cancel_membership`,
  `search_orders`, `get_order`, `request_return`. Skills: `prorated-refund-calculator`,
  `points-reconciliation`, `slip-pdf-generator`.
- **Self-Serve Card Reissue** — open **Returns & Service Assistant, Preview** and
  paste the 3 turns from
  `sample/archive/store-solution/evals/self-serve-card-reissue.md`. Expect identity
  verification, the old card deactivated, a new card serial, and a generated PNG
  card. Tools: `get_membership`, `reissue_card`. Skills: `card-reissue`,
  `membership-card-png`.

The Python skills ride in on the agents solution and register on `PublishAllXml`;
no manual skill upload is needed. (If a skill ever lands present-but-broken in some
env, re-upload its zip from `sample/solution/skills/` via the agent's **Add a
skill** dialog and republish — the portal recompiles the bundle.)

## Configuration

`deploy/manifest.json` holds the declarative metadata:

- `solutions` — the two zips to import, in order, with their target unique names.
- `connectors` — slug, display name, connector id, and `settlePass` flag per MCP
  connector. The connector files live under `sample/solution/connectors/<slug>/`
  (`apiDefinition.json`, `apiProperties.json`, `script.csx`).
- `agents` — schema name, display name, role (child/parent), and the MCP server(s)
  each agent re-attaches in the manual step.
- `import` retry/timeout and `apimPropagationSeconds` tuning.

Edit it if the solution contents change.

## Why two solutions?

The connectors and the agents have different lifecycles and the MCP connection
references don't export cleanly from the new authoring UI (they're born in the CDS
Default Solution and export with no edges). Splitting them keeps the connectors —
whose identity the agents' tools reference — in their own stable solution, while
the agents solution is sanitized to strip the un-exportable MCP tools. The cost is
the one manual re-attach step above, which recreates a fresh, working tool binding
against the connection that already exists. This is the only flow validated end to
end.

## Findings (the "deployment process" problems, resolved)

1. **Import exceeds pac's 30-minute client timeout.** Compiling the inline MCP
   connectors routinely trips `The request channel timed out ... 00:30:00`, even
   though the server-side import job keeps running and completes. The import step
   polls Dataverse and treats the solution's presence as success instead of trusting
   pac's exit code. (Also: the US custom-code function-app pool can be
   capacity-exhausted, `Unable to find an unassigned function app in 'East US'`, so
   we deploy to **EU**.)

2. **Back-to-back imports collide.** Importing the second solution while the first
   is still finalising async fails with "Cannot start another Import because there is
   a previous Import running". Fix: poll `importjobs` until the first import reports
   `completedon` before starting the next.

3. **Import does not deploy the connectors' inline code.** Solution import registers
   each custom-code connector but does not compile/deploy its `.csx`; the connector's
   `modifiedon` stays equal to `createdon` and tools fail to load. Fix:
   `pac connector update` per connector from the bundled files, verifying `modifiedon`
   advanced, with a deadline + retry (pac can report "succesfully" without deploying,
   or hang).

4. **Connectors don't appear in the modern MCP picker until you publish.** After
   `pac connector update` you **must** run Dataverse `PublishAllXml`, otherwise the
   custom-code MCP connectors never surface in "Add a tool, Model Context Protocol".
   This single missing step was the original blocker; it's now step 2.

5. **The big Warehouse connector can bind stale code.** After its first deploy the
   7-tool Warehouse connector showed in the picker but 500'd at runtime. A second
   deploy + publish (the manifest `settlePass`) re-binds the active revision. Only
   Warehouse is flagged, to keep deploys fast.

6. **Tool binding needs no UI binding and no guid-matching.** With `authMode: Maker`
   the runtime resolves any Connected maker connection for the tool's connector, so
   the connections step just creates one no-auth connection per connector and the
   agents' source-env `connectorId` hashes still resolve.
