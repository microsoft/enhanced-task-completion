# Enhanced Task Completion — Deployable Sample

An e-commerce customer service demo for **Enhanced Task Completion** in Microsoft Copilot Studio. Two agents chain 9 tools across two inline MCP connectors — everything runs inside the Power Platform, no external servers needed.

## What's included

| Component | Description |
|---|---|
| **ETC - Order Management** | Primary agent. Searches orders, views details, tracks shipments, manages returns. Delegates warehouse queries to the connected agent below. |
| **ETC - Warehouse Management** | Connected agent for inventory and fulfillment. Checks stock levels, tracks fulfillment pipeline, finds alternatives, looks up restock dates. |
| **Order Management MCP** | Custom connector with inline C# MCP server. 5 tools: `search_orders`, `get_order`, `get_shipment`, `request_return`, `get_return_status` |
| **Warehouse MCP** | Custom connector with inline C# MCP server. 4 tools: `check_stock`, `get_fulfillment_status`, `find_alternatives`, `get_restock_date` |

## Quick start

### 1. Deploy the connectors

The MCP connectors run as inline C# scripts inside custom connectors — no external servers or dev tunnels required. Deploy them using the Power Platform CLI:

```bash
# Install PAC CLI if you don't have it: https://aka.ms/PowerPlatformCLI

# Authenticate to your environment
pac auth create --environment https://YOUR-ORG.crm.dynamics.com

# Deploy Order Management MCP connector
cd connectors/order-management-inline
pac connector create \
  --api-definition-file apiDefinition.swagger.json \
  --api-properties-file apiProperties.json \
  --script-file script.csx

# Deploy Warehouse MCP connector
cd ../warehouse-inline
pac connector create \
  --api-definition-file apiDefinition.swagger.json \
  --api-properties-file apiProperties.json \
  --script-file script.csx
```

### 2. Import the solution

1. Go to [make.powerapps.com](https://make.powerapps.com) and select your environment
2. Navigate to **Solutions** > **Import solution**
3. Upload `solution/EnhancedTaskCompletionDemo.zip`
4. Click **Next**, then **Import**

### 3. Create connections

Go to **Custom connectors** in the left nav. For each connector (**Order Management MCP** and **Warehouse MCP**), click **Create connection** — no auth needed, just click **Create**.

### 4. Wire up the tools

In Copilot Studio, open each agent and add the MCP tools:

- **ETC - Order Management**: Add the **Order Management MCP** connector as an MCP tool
- **ETC - Warehouse Management**: Add the **Warehouse MCP** connector as an MCP tool

### 5. Publish and test

Publish both agents, then open **ETC - Order Management** and try these prompts:

> Hi, I'm Sarah Mitchell. I ordered some Sony headphones recently but they arrived with a crackling sound in the left ear. I'd like to return them.

Tests: `search_orders` -> `get_order` (x3) -> `request_return` — a multi-step return flow.

> I'm Emily Chen. I returned a damaged Blu-ray disc a couple weeks ago — can you check if my refund has been processed yet, and also tell me where my ergonomic chair delivery is right now?

Tests: `search_orders` -> `get_order` -> `get_return_status` + `get_shipment` — return tracking and delivery tracking in one conversation.

> I'm James Rivera. I have two pending orders — can you give me a full status update on both? I want to know exactly where each one is in the process, when they'll ship, and if anything is out of stock, what alternatives do I have?

Tests the full cross-agent flow: `search_orders` -> `get_order` (x2) -> `get_shipment` + **Warehouse Agent** delegation (in parallel).

> I'm about to upload a CSV with order IDs. For each order, fill in all the empty columns and return the completed CSV.

Upload [`chat-ui/data/demo-orders.csv`](chat-ui/data/demo-orders.csv) with this prompt. Tests file upload + multi-tool chaining to enrich a spreadsheet.

## How it works

The connectors use the [Power MCP Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template) pattern. A C# script (`script.csx`) inside each custom connector implements a full MCP server that handles `initialize`, `tools/list`, and `tools/call` requests with static mock data.

When Copilot Studio calls the connector, the script processes the MCP request and returns structured JSON responses. No external MCP servers, no dev tunnels, no Node.js — the connector *is* the MCP server.

### Connector source

| Connector | Script | Tools |
|---|---|---|
| Order Management MCP | [`connectors/order-management-inline/script.csx`](connectors/order-management-inline/script.csx) | search_orders, get_order, get_shipment, request_return, get_return_status |
| Warehouse MCP | [`connectors/warehouse-inline/script.csx`](connectors/warehouse-inline/script.csx) | check_stock, get_fulfillment_status, find_alternatives, get_restock_date |

Based on [Power MCP Template v2.1](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template) by Troy Taylor (MIT License).

## Optional: Gradio Chat UI

The `chat-ui/` folder contains a Python frontend that renders reasoning steps, tool calls, and file attachments inline. It connects to the agent via the Copilot Studio SDK and requires an Entra ID App Registration with `CopilotStudio.Copilots.Invoke` permission.

```bash
cp chat-ui/.env.sample chat-ui/.env
# Edit .env with your environment ID, agent schema name, tenant ID, and client ID
pip install -r chat-ui/requirements.txt
python chat-ui/app.py
```

## Prerequisites

- A Power Platform environment with Copilot Studio
- Maker or Admin role in the target environment
- [Power Platform CLI](https://aka.ms/PowerPlatformCLI) for deploying connectors
