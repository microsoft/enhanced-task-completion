# Enhanced Task Completion

A showcase site and deployable sample for **Enhanced Task Completion** in Microsoft Copilot Studio.

**Live site**: https://microsoft.github.io/enhanced-task-completion/

## What's in this repo

| Folder | Description |
|---|---|
| `src/` | Astro site — landing page, scenario walkthroughs, and documentation |
| `sample/` | Deployable sample — two agents, two inline MCP connectors, one solution zip |

## Deploying the sample

The sample includes two Copilot Studio agents that chain 9 tools across two MCP connectors for an e-commerce customer service scenario. Everything runs inside the Power Platform — the connectors use inline C# scripts, so no external servers are needed.

```
sample/
  solution/          Solution zip — import into any Power Platform environment
  connectors/        Inline MCP connector source (C# scripts + swagger)
  chat-ui/           Optional Gradio frontend with reasoning + tool call rendering
```

See [`sample/README.md`](./sample/README.md) for step-by-step setup.

## Site development

```bash
npm install
npm run dev        # http://localhost:4321/enhanced-task-completion/
npm run build      # Build to ./dist/
```

## Contributing

This project welcomes contributions and suggestions. See [CONTRIBUTING](https://github.com/microsoft/enhanced-task-completion/blob/main/CONTRIBUTING.md) for details.

## License

MIT License. Copyright (c) Microsoft Corporation.
