# Enhanced Task Completion — Sample

An e-commerce customer service demo for **Enhanced Task Completion** in Microsoft Copilot Studio. Two agents chain 9 tools across two inline MCP connectors — everything runs inside the Power Platform, no external servers needed.

## What's in the solution

| Component | Description |
|---|---|
| **ETC - Order Management** | Primary agent. Searches orders, views details, tracks shipments, manages returns. Delegates warehouse queries to the connected agent. |
| **ETC - Warehouse Management** | Connected agent for inventory and fulfillment. Checks stock, tracks fulfillment pipeline, finds alternatives, looks up restock dates. |
| **Order Management MCP** | Custom connector with inline MCP server (C# script). 5 tools with mock e-commerce data. |
| **Warehouse MCP** | Custom connector with inline MCP server (C# script). 4 tools with mock warehouse data. |

## Quick start

### 1. Import the solution

1. Go to [make.powerapps.com](https://make.powerapps.com) and select your environment
2. Navigate to **Solutions** > **Import solution**
3. Upload `solution/EnhancedTaskCompletionDemo.zip`
4. Click **Next**, then **Import**

### 2. Create connections

After import, go to **Custom connectors** in the left nav. For each MCP connector (**Order Management MCP** and **Warehouse MCP**), click **Create connection** — no auth needed, just click **Create**.

### 3. Publish agents

In Copilot Studio, open each agent (**ETC - Order Management** and **ETC - Warehouse Management**) and click **Publish**.

### 4. Test

Open **ETC - Order Management** in Copilot Studio and try these prompts in the test pane:

> Hi, I'm Sarah Mitchell. I ordered some Sony headphones recently but they arrived with a crackling sound in the left ear. I'd like to return them. Also, can you check where my other order is — the Kindle I ordered last week?

> I want to return something I bought recently.

Tests conversational slot-filling: the agent asks which order, what's wrong, and confirms before calling any tools.

> I'm James Rivera. I ordered a Nintendo Switch bundle about 10 days ago and it still hasn't shipped. What's going on?

Tests cross-agent delegation: Order agent checks with Warehouse, discovers out-of-stock item, asks user about alternatives, delegates back to Warehouse — a multi-turn cross-agent conversation.

> I'm about to upload a CSV with order IDs. For each order, fill in all the empty columns and return the completed CSV.

For the CSV prompt, upload [`chat-ui/data/demo-orders.csv`](chat-ui/data/demo-orders.csv).

## Optional: Gradio Chat UI

The `chat-ui/` folder contains a Python frontend that renders reasoning steps, tool calls, and file attachments inline — useful for testing outside Copilot Studio. It requires an Entra ID App Registration with `CopilotStudio.Copilots.Invoke` permission.

```bash
cp chat-ui/.env.sample chat-ui/.env
# Edit .env with your environment ID, agent schema name, tenant ID, and client ID
pip install -r chat-ui/requirements.txt
python chat-ui/app.py
```

## How it works

The connectors use the [Power MCP Template](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template) pattern — a C# script inside each custom connector implements a full MCP server. When Copilot Studio calls the connector, the script handles `initialize`, `tools/list`, and `tools/call` with static mock data. No external servers, no dev tunnels, no Node.js.

The connector source is in `connectors/` for reference:

| Connector | Script | Tools |
|---|---|---|
| Order Management MCP | [`connectors/order-management-inline/script.csx`](connectors/order-management-inline/script.csx) | search_orders, get_order, get_shipment, request_return, get_return_status |
| Warehouse MCP | [`connectors/warehouse-inline/script.csx`](connectors/warehouse-inline/script.csx) | check_stock, get_fulfillment_status, find_alternatives, get_restock_date |

Based on [Power MCP Template v2.1](https://github.com/troystaylor/SharingIsCaring/tree/main/Connector-Code/Power%20MCP%20Template) by Troy Taylor (MIT License).

## Prerequisites

- A Power Platform environment with Copilot Studio
- Maker or Admin role in the target environment
