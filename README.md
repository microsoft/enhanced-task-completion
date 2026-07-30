# Copilot Studio Technical Guide

A showcase site and deployable sample for the Agents and Workflows experience in Microsoft Copilot Studio.

**Live site**: https://microsoft.github.io/new-copilot-studio-tech-guide/

## What's in this repo

| Folder | Description |
|---|---|
| `src/` | Astro site — landing page, scenario walkthroughs, and documentation |
| `deploy/` | Scripted, repeatable deploy of the sample into a Power Platform environment |
| `sample/` | Deployable sample — the Copilot Studio solution (`sample/solution/`) plus archived earlier iterations (`sample/archive/`) |

## Deploying the sample

Four agents (flagship Store Associate Assistant, self-serve Returns & Service Assistant,
and two connected agents) and four inline MCP connectors (Membership, Order Management,
Policy RAG, Warehouse). Everything runs inside the Power Platform: no external servers.

Stand it up with one cross-platform script (needs **Node 18+**, **pac CLI**, and **az
CLI** installed):

```bash
pac auth create                   # once: sign pac in to the target tenant
node deploy/deploy.mjs            # guided: pick profile, pick env, deploy
node deploy/deploy.mjs --help     # all options
```

It imports both solutions, deploys the connector code, creates the connections, and
publishes the agents, then prints one ~2-minute manual UI step.

```
deploy/             Scripted, repeatable deploy (deploy.mjs + README)
sample/
  solution/         The two solution zips + unpacked source + connector code + skills
  archive/          Earlier iterations (connectors, store-solution, chat UI, exports)
```

See [`deploy/README.md`](./deploy/README.md) for the full walkthrough and the manual
re-attach step, and [`sample/solution/README.md`](./sample/solution/README.md) for what's
in the solution and the two demo scenarios (Self-Serve Card Reissue and Block Party
Trade-Up).

## Site development

```bash
npm install
npm run dev        # http://localhost:4321/new-copilot-studio-tech-guide/
npm run build      # Build to ./dist/
```

Site analytics use [Microsoft Clarity](https://clarity.microsoft.com/), loaded in
production builds only (never on `npm run dev`). Override the project id with the
`PUBLIC_CLARITY_ID` env var — see [`.env.example`](./.env.example).

## Contributing

This project welcomes contributions and suggestions. See [CONTRIBUTING](https://github.com/microsoft/new-copilot-studio-tech-guide/blob/main/CONTRIBUTING.md) for details.

## License

MIT License. Copyright (c) Microsoft Corporation.
