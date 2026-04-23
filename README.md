# Enhanced Task Completion

A showcase site and deployable sample for **Enhanced Task Completion** in Microsoft Copilot Studio.

**Live site**: https://microsoft.github.io/enhanced-task-completion/

## What's in this repo

| Folder | Description |
|---|---|
| `src/` | Astro site — landing page, scenario walkthroughs, and documentation |
| `sample/` | Deployable sample — MCP servers, Copilot Studio agents, Gradio chat UI, and setup scripts |

## Site development

```bash
npm install
npm run dev        # http://localhost:4321/enhanced-task-completion/
npm run build      # Build to ./dist/
```

## Running the sample

See [`sample/README.md`](./sample/README.md) for full setup instructions. Quick version:

```bash
cd sample
node scripts/setup.mjs          # Install dependencies
node scripts/start.mjs           # Start MCP servers + devtunnels
node scripts/start-ui.mjs        # Start Gradio chat UI
```

## Contributing

This project welcomes contributions and suggestions. See [CONTRIBUTING](https://github.com/microsoft/enhanced-task-completion/blob/main/CONTRIBUTING.md) for details.

## License

MIT License. Copyright (c) Microsoft Corporation.
