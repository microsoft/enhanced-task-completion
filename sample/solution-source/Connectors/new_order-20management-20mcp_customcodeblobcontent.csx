using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

// ╔══════════════════════════════════════════════════════════════════════════════╗
// ║  Order Management MCP Connector (inline)                                    ║
// ║                                                                            ║
// ║  5 tools with static mock data — no external server needed.                ║
// ║  Based on Power MCP Template v2.1 by Troy Taylor.                          ║
// ╚══════════════════════════════════════════════════════════════════════════════╝

public class Script : ScriptBase
{


    private static readonly McpServerOptions Options = new McpServerOptions
    {
        ServerInfo = new McpServerInfo
        {
            Name = "order-management",
            Version = "1.0.0",
            Title = "Order Management",
            Description = "E-commerce order management with tools for searching orders, viewing details, tracking shipments, and managing returns."
        },
        ProtocolVersion = "2025-11-25",
        Capabilities = new McpCapabilities { Tools = true },
        Instructions = "Use search_orders first to find orders by customer name, email, or order number. Then use the order_id from results with get_order, get_shipment, request_return, or get_return_status."
    };

    public override async Task<HttpResponseMessage> ExecuteAsync()
    {
        var handler = new McpRequestHandler(Options);
        RegisterCapabilities(handler);

        var body = await this.Context.Request.Content.ReadAsStringAsync().ConfigureAwait(false);
        var result = await handler.HandleAsync(body, this.CancellationToken).ConfigureAwait(false);

        return new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(result, Encoding.UTF8, "application/json")
        };
    }

    // ── Static Data ─────────────────────────────────────────────────────

    private static readonly JArray Orders = JArray.Parse(@"[
        {""id"":""ORD-10421"",""customer"":{""id"":""C-001"",""name"":""Sarah Mitchell"",""email"":""sarah.mitchell@example.com""},""date"":""2026-04-10"",""status"":""shipped"",""items"":[{""sku"":""SKU-APEX5"",""name"":""Apex NoiseGuard 5 Headphones"",""quantity"":1,""unitPrice"":349.99},{""sku"":""SKU-USBC3"",""name"":""USB-C Charging Cable (3-pack)"",""quantity"":1,""unitPrice"":14.99}],""shippingAddress"":""742 Evergreen Terrace, Springfield, IL 62704"",""paymentMethod"":""Visa ending in 4242"",""total"":364.98},
        {""id"":""ORD-10422"",""customer"":{""id"":""C-001"",""name"":""Sarah Mitchell"",""email"":""sarah.mitchell@example.com""},""date"":""2026-04-15"",""status"":""processing"",""items"":[{""sku"":""SKU-LUMI"",""name"":""LumiRead E-Reader (16GB)"",""quantity"":1,""unitPrice"":149.99}],""shippingAddress"":""742 Evergreen Terrace, Springfield, IL 62704"",""paymentMethod"":""Visa ending in 4242"",""total"":149.99},
        {""id"":""ORD-10318"",""customer"":{""id"":""C-001"",""name"":""Sarah Mitchell"",""email"":""sarah.mitchell@example.com""},""date"":""2026-03-22"",""status"":""delivered"",""items"":[{""sku"":""SKU-PULSE"",""name"":""PulseWave Pro Earbuds"",""quantity"":1,""unitPrice"":249.00},{""sku"":""SKU-CASE01"",""name"":""Silicone Earbuds Case - Midnight"",""quantity"":1,""unitPrice"":19.99}],""shippingAddress"":""742 Evergreen Terrace, Springfield, IL 62704"",""paymentMethod"":""Visa ending in 4242"",""total"":268.99},
        {""id"":""ORD-10455"",""customer"":{""id"":""C-002"",""name"":""James Rivera"",""email"":""j.rivera@example.com""},""date"":""2026-04-12"",""status"":""shipped"",""items"":[{""sku"":""SKU-HOODIE"",""name"":""TrailMark Fleece Hoodie - Black (L)"",""quantity"":1,""unitPrice"":120.00},{""sku"":""SKU-JOGGER"",""name"":""TrailMark Sport Joggers - Grey (L)"",""quantity"":1,""unitPrice"":85.00}],""shippingAddress"":""88 Sunset Blvd, Apt 4B, Los Angeles, CA 90028"",""paymentMethod"":""Mastercard ending in 8811"",""total"":205.00},
        {""id"":""ORD-10460"",""customer"":{""id"":""C-002"",""name"":""James Rivera"",""email"":""j.rivera@example.com""},""date"":""2026-04-18"",""status"":""processing"",""items"":[{""sku"":""SKU-VORTEX"",""name"":""Vortex Gaming Console OLED"",""quantity"":1,""unitPrice"":349.99},{""sku"":""SKU-REALM"",""name"":""Realm of Legends: The Lost Crown"",""quantity"":1,""unitPrice"":59.99}],""shippingAddress"":""88 Sunset Blvd, Apt 4B, Los Angeles, CA 90028"",""paymentMethod"":""Mastercard ending in 8811"",""total"":409.98},
        {""id"":""ORD-10389"",""customer"":{""id"":""C-003"",""name"":""Emily Chen"",""email"":""emily.chen@example.com""},""date"":""2026-03-28"",""status"":""delivered"",""items"":[{""sku"":""SKU-STAR2"",""name"":""Starfall: Part Two (4K Blu-ray)"",""quantity"":1,""unitPrice"":29.99},{""sku"":""SKU-ETHER"",""name"":""The Ether Expanse (R. Caldwell) - Paperback"",""quantity"":1,""unitPrice"":12.99},{""sku"":""SKU-QPRDX"",""name"":""The Quantum Paradox - Paperback"",""quantity"":1,""unitPrice"":14.99}],""shippingAddress"":""1200 Main Street, Unit 7C, Seattle, WA 98101"",""paymentMethod"":""Amex ending in 3003"",""total"":57.97},
        {""id"":""ORD-10478"",""customer"":{""id"":""C-003"",""name"":""Emily Chen"",""email"":""emily.chen@example.com""},""date"":""2026-04-14"",""status"":""shipped"",""items"":[{""sku"":""SKU-COMFT"",""name"":""ComfortEdge Office Chair - Mesh Back"",""quantity"":1,""unitPrice"":299.00}],""shippingAddress"":""1200 Main Street, Unit 7C, Seattle, WA 98101"",""paymentMethod"":""Amex ending in 3003"",""total"":299.00}
    ]");

    private static readonly JObject Shipments = JObject.Parse(@"{
        ""ORD-10421"":{""order_id"":""ORD-10421"",""carrier"":""SwiftShip"",""tracking_number"":""SS-794644790132"",""tracking_url"":""https://track.swiftship.example.com/SS-794644790132"",""estimated_delivery"":""2026-04-22"",""last_update"":""2026-04-20T14:30:00Z"",""status"":""out_for_delivery""},
        ""ORD-10455"":{""order_id"":""ORD-10455"",""carrier"":""PrimeFreight"",""tracking_number"":""PF-10123456784"",""tracking_url"":""https://track.primefreight.example.com/PF-10123456784"",""estimated_delivery"":""2026-04-21"",""last_update"":""2026-04-19T09:15:00Z"",""status"":""in_transit""},
        ""ORD-10318"":{""order_id"":""ORD-10318"",""carrier"":""NationPost"",""tracking_number"":""NP-223100287654"",""tracking_url"":""https://track.nationpost.example.com/NP-223100287654"",""estimated_delivery"":""2026-03-28"",""last_update"":""2026-03-28T10:15:00Z"",""status"":""delivered""},
        ""ORD-10478"":{""order_id"":""ORD-10478"",""carrier"":""SwiftShip"",""tracking_number"":""SS-794644790199"",""tracking_url"":""https://track.swiftship.example.com/SS-794644790199"",""estimated_delivery"":""2026-04-24"",""last_update"":""2026-04-21T10:00:00Z"",""status"":""in_transit""}
    }");

    private static readonly JObject Returns = JObject.Parse(@"{
        ""RA-50012"":{""return_id"":""RA-50012"",""order_id"":""ORD-10318"",""status"":""refund_processed"",""items_returned"":[{""sku"":""SKU-CASE01"",""name"":""Silicone Earbuds Case - Midnight""}],""reason"":""Wrong color received"",""refund_amount"":""$19.99"",""refund_method"":""Visa ending in 4242""},
        ""RA-50018"":{""return_id"":""RA-50018"",""order_id"":""ORD-10389"",""status"":""received"",""items_returned"":[{""sku"":""SKU-STAR2"",""name"":""Starfall: Part Two (4K Blu-ray)""}],""reason"":""Disc scratched on arrival"",""refund_amount"":""$29.99"",""refund_method"":""Amex ending in 3003""}
    }");

    private static int _returnCounter = 50019;

    // ── Tool Registration ───────────────────────────────────────────────

    private void RegisterCapabilities(McpRequestHandler handler)
    {
        // 1. search_orders
        handler.AddTool("search_orders",
            "Search for orders by customer name, email, or order number. Returns a summary list. This is the entry point — use it first to find order IDs.",
            schemaConfig: s => s.String("query", "Customer name, email address, or order number to search for", required: true),
            handler: async (args, ct) =>
            {
                var query = (args.Value<string>("query") ?? "").ToLower();
                var matches = new JArray();
                foreach (var order in Orders)
                {
                    var name = order["customer"]?["name"]?.ToString().ToLower() ?? "";
                    var email = order["customer"]?["email"]?.ToString().ToLower() ?? "";
                    var id = order["id"]?.ToString().ToLower() ?? "";
                    if (name.Contains(query) || email.Contains(query) || id.Contains(query))
                    {
                        matches.Add(new JObject
                        {
                            ["order_id"] = order["id"],
                            ["date"] = order["date"],
                            ["status"] = order["status"],
                            ["total"] = "$" + order["total"],
                            ["customer"] = order["customer"]?["name"],
                            ["item_count"] = (order["items"] as JArray)?.Count ?? 0
                        });
                    }
                }
                if (matches.Count == 0)
                    return new JObject { ["message"] = $"No orders found matching \"{query}\"." };
                return new JObject { ["orders"] = matches };
            });

        // 2. get_order
        handler.AddTool("get_order",
            "Get full details for a specific order including line items, shipping address, and payment info. Use an order_id from search_orders results.",
            schemaConfig: s => s.String("order_id", "Order ID (e.g. ORD-10421) from search_orders results", required: true),
            handler: async (args, ct) =>
            {
                var orderId = args.Value<string>("order_id") ?? "";
                foreach (var order in Orders)
                {
                    if (order["id"]?.ToString() == orderId)
                        return JObject.Parse(order.ToString());
                }
                throw new ArgumentException($"Order \"{orderId}\" not found.");
            });

        // 3. get_shipment
        handler.AddTool("get_shipment",
            "Get shipment tracking info for an order. Only available for shipped/delivered orders. Returns carrier, tracking number, URL, and delivery estimate.",
            schemaConfig: s => s.String("order_id", "Order ID (e.g. ORD-10421)", required: true),
            handler: async (args, ct) =>
            {
                var orderId = args.Value<string>("order_id") ?? "";
                if (Shipments[orderId] != null)
                    return JObject.Parse(Shipments[orderId].ToString());

                // Check if order exists but isn't shipped
                foreach (var order in Orders)
                {
                    if (order["id"]?.ToString() == orderId)
                        throw new ArgumentException($"Order \"{orderId}\" has status \"{order["status"]}\" — shipment tracking is only available for shipped or delivered orders.");
                }
                throw new ArgumentException($"Order \"{orderId}\" not found.");
            });

        // 4. request_return
        handler.AddTool("request_return",
            "Initiate a return for specific items in an order. Returns a return authorization with ID, label, refund estimate, and instructions.",
            schemaConfig: s => s
                .String("order_id", "Order ID to return items from", required: true)
                .Array("item_skus", "SKUs of items to return (from get_order line items)", itemSchema: new JObject { ["type"] = "string" }, required: true)
                .String("reason", "Reason for return (e.g. 'Defective', 'Wrong item')", required: true),
            handler: async (args, ct) =>
            {
                var orderId = args.Value<string>("order_id") ?? "";
                var reason = args.Value<string>("reason") ?? "Not specified";
                var skuArray = args["item_skus"] as JArray ?? new JArray();
                var skus = skuArray.Select(s => s.ToString()).ToList();

                foreach (var order in Orders)
                {
                    if (order["id"]?.ToString() != orderId) continue;

                    var items = new JArray();
                    double refundTotal = 0;
                    foreach (var item in order["items"] as JArray ?? new JArray())
                    {
                        if (skus.Contains(item["sku"]?.ToString()))
                        {
                            items.Add(new JObject { ["sku"] = item["sku"], ["name"] = item["name"] });
                            refundTotal += item["unitPrice"]?.Value<double>() ?? 0;
                        }
                    }

                    var returnId = $"RA-{System.Threading.Interlocked.Increment(ref _returnCounter):D5}";
                    return new JObject
                    {
                        ["return_id"] = returnId,
                        ["order_id"] = orderId,
                        ["status"] = "requested",
                        ["items_returned"] = items,
                        ["reason"] = reason,
                        ["refund_amount"] = $"${refundTotal:F2}",
                        ["refund_method"] = order["paymentMethod"],
                        ["return_label_url"] = $"https://returns.example.com/labels/{returnId}.pdf",
                        ["instructions"] = "Print the return label, attach it to the package, and drop it off at any carrier location within 14 days."
                    };
                }
                throw new ArgumentException($"Order \"{orderId}\" not found.");
            });

        // 5. get_return_status
        handler.AddTool("get_return_status",
            "Check the status of a return request. Returns current stage, refund status, and timeline.",
            schemaConfig: s => s.String("return_id", "Return ID (e.g. RA-50019) from request_return result", required: true),
            handler: async (args, ct) =>
            {
                var returnId = args.Value<string>("return_id") ?? "";
                if (Returns[returnId] != null)
                    return JObject.Parse(Returns[returnId].ToString());

                // For newly created returns, return a generic status
                return new JObject
                {
                    ["return_id"] = returnId,
                    ["status"] = "requested",
                    ["refund_status"] = "pending",
                    ["timeline"] = new JArray { new JObject { ["stage"] = "Return requested", ["date"] = DateTime.UtcNow.ToString("yyyy-MM-dd") } }
                };
            });
    }

}

// ║  SECTION 2: MCP FRAMEWORK                                                  ║
// ║                                                                            ║
// ║  Built-in McpRequestHandler that brings MCP C# SDK patterns to Power       ║
// ║  Platform. If Microsoft enables the official SDK namespaces, this section   ║
// ║  becomes a using statement instead of inline code.                          ║
// ║                                                                            ║
// ║  Spec coverage: MCP 2025-11-25                                             ║
// ║  Handles: initialize, ping, tools/*, resources/*, prompts/*,               ║
// ║           completion/complete, logging/setLevel, all notifications          ║
// ║                                                                            ║
// ║  Stateless limitations (Power Platform cannot send async notifications):   ║
// ║   - Tasks (experimental, requires persistent state between requests)       ║
// ║   - Server→client requests (sampling, elicitation, roots/list)             ║
// ║   - Server→client notifications (progress, logging/message, list_changed)  ║
// ║                                                                            ║
// ║  Do not modify unless extending the framework itself.                      ║
// ╚══════════════════════════════════════════════════════════════════════════════╝

// ── Configuration Types ──────────────────────────────────────────────────────

/// <summary>Server identity reported in initialize response.</summary>
public class McpServerInfo
{
    public string Name { get; set; } = "mcp-server";
    public string Version { get; set; } = "1.0.0";
    public string Title { get; set; }
    public string Description { get; set; }
}

/// <summary>Capabilities declared during initialization.</summary>
public class McpCapabilities
{
    public bool Tools { get; set; } = true;
    public bool Resources { get; set; }
    public bool Prompts { get; set; }
    public bool Logging { get; set; }
    public bool Completions { get; set; }
}

/// <summary>Top-level configuration for the MCP handler.</summary>
public class McpServerOptions
{
    public McpServerInfo ServerInfo { get; set; } = new McpServerInfo();
    public string ProtocolVersion { get; set; } = "2025-11-25";
    public McpCapabilities Capabilities { get; set; } = new McpCapabilities();
    public string Instructions { get; set; }
}

// ── Error Handling ───────────────────────────────────────────────────────────

/// <summary>Standard JSON-RPC 2.0 error codes used by MCP.</summary>
public enum McpErrorCode
{
    RequestTimeout = -32000,
    ParseError = -32700,
    InvalidRequest = -32600,
    MethodNotFound = -32601,
    InvalidParams = -32602,
    InternalError = -32603
}

/// <summary>
/// Throw from tool methods to surface a structured MCP error.
/// Mirrors ModelContextProtocol.McpException from the official SDK.
/// </summary>
public class McpException : Exception
{
    public McpErrorCode Code { get; }
    public McpException(McpErrorCode code, string message) : base(message) => Code = code;
}

// ── Schema Builder (Fluent API) ──────────────────────────────────────────────

/// <summary>Fluent builder for JSON Schema objects used in tool inputSchema.</summary>
public class McpSchemaBuilder
{
    private readonly JObject _properties = new JObject();
    private readonly JArray _required = new JArray();

    public McpSchemaBuilder String(string name, string description, bool required = false, string format = null, string[] enumValues = null)
    {
        var prop = new JObject { ["type"] = "string", ["description"] = description };
        if (format != null) prop["format"] = format;
        if (enumValues != null) prop["enum"] = new JArray(enumValues);
        _properties[name] = prop;
        if (required) _required.Add(name);
        return this;
    }

    public McpSchemaBuilder Integer(string name, string description, bool required = false, int? defaultValue = null)
    {
        var prop = new JObject { ["type"] = "integer", ["description"] = description };
        if (defaultValue.HasValue) prop["default"] = defaultValue.Value;
        _properties[name] = prop;
        if (required) _required.Add(name);
        return this;
    }

    public McpSchemaBuilder Number(string name, string description, bool required = false)
    {
        _properties[name] = new JObject { ["type"] = "number", ["description"] = description };
        if (required) _required.Add(name);
        return this;
    }

    public McpSchemaBuilder Boolean(string name, string description, bool required = false)
    {
        _properties[name] = new JObject { ["type"] = "boolean", ["description"] = description };
        if (required) _required.Add(name);
        return this;
    }

    public McpSchemaBuilder Array(string name, string description, JObject itemSchema, bool required = false)
    {
        _properties[name] = new JObject
        {
            ["type"] = "array",
            ["description"] = description,
            ["items"] = itemSchema
        };
        if (required) _required.Add(name);
        return this;
    }

    public McpSchemaBuilder Object(string name, string description, Action<McpSchemaBuilder> nestedConfig, bool required = false)
    {
        var nested = new McpSchemaBuilder();
        nestedConfig?.Invoke(nested);
        var obj = nested.Build();
        obj["description"] = description;
        _properties[name] = obj;
        if (required) _required.Add(name);
        return this;
    }

    public JObject Build()
    {
        var schema = new JObject
        {
            ["type"] = "object",
            ["properties"] = _properties
        };
        if (_required.Count > 0) schema["required"] = _required;
        return schema;
    }
}

// ── Internal Tool Registration ───────────────────────────────────────────────

internal class McpToolDefinition
{
    public string Name { get; set; }
    public string Title { get; set; }
    public string Description { get; set; }
    public JObject InputSchema { get; set; }
    public JObject OutputSchema { get; set; }
    public JObject Annotations { get; set; }
    public Func<JObject, CancellationToken, Task<object>> Handler { get; set; }
}

// ── Internal Resource Registration ───────────────────────────────────────────

internal class McpResourceDefinition
{
    public string Uri { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public string MimeType { get; set; }
    public JObject Annotations { get; set; }
    public Func<CancellationToken, Task<JArray>> Handler { get; set; }
}

internal class McpResourceTemplateDefinition
{
    public string UriTemplate { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public string MimeType { get; set; }
    public JObject Annotations { get; set; }
    public Func<string, CancellationToken, Task<JArray>> Handler { get; set; }
}

// ── Internal Prompt Registration ─────────────────────────────────────────────

/// <summary>Describes a single prompt argument.</summary>
public class McpPromptArgument
{
    public string Name { get; set; }
    public string Description { get; set; }
    public bool Required { get; set; }
}

internal class McpPromptDefinition
{
    public string Name { get; set; }
    public string Description { get; set; }
    public List<McpPromptArgument> Arguments { get; set; } = new List<McpPromptArgument>();
    public Func<JObject, CancellationToken, Task<JArray>> Handler { get; set; }
}

// ── McpRequestHandler ────────────────────────────────────────────────────────
//
//    The core bridge class. Stateless, no DI, no ASP.NET Core.
//    Takes a JSON-RPC string in → returns a JSON-RPC string out.
//    This is the class that does not exist in the official SDK today.
//

/// <summary>
/// Stateless MCP request handler that bridges the official SDK's patterns
/// to Power Platform's ScriptBase.ExecuteAsync() model.
/// 
/// Handles all JSON-RPC 2.0 routing, protocol negotiation, tool discovery,
/// parameter binding, and response formatting internally.
/// </summary>
public class McpRequestHandler
{
    private readonly McpServerOptions _options;
    private readonly Dictionary<string, McpToolDefinition> _tools;
    private readonly Dictionary<string, McpResourceDefinition> _resources;
    private readonly List<McpResourceTemplateDefinition> _resourceTemplates;
    private readonly Dictionary<string, McpPromptDefinition> _prompts;

    /// <summary>
    /// Optional logging callback. Wire this up to Application Insights,
    /// Context.Logger, or any other telemetry sink.
    /// </summary>
    public Action<string, object> OnLog { get; set; }

    public McpRequestHandler(McpServerOptions options)
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _tools = new Dictionary<string, McpToolDefinition>(StringComparer.OrdinalIgnoreCase);
        _resources = new Dictionary<string, McpResourceDefinition>(StringComparer.OrdinalIgnoreCase);
        _resourceTemplates = new List<McpResourceTemplateDefinition>();
        _prompts = new Dictionary<string, McpPromptDefinition>(StringComparer.OrdinalIgnoreCase);
    }

    // ── Tool Registration ────────────────────────────────────────────────

    /// <summary>
    /// Register a tool using the fluent API.
    /// Define the schema with McpSchemaBuilder, provide a handler, and optionally set annotations.
    /// </summary>
    public McpRequestHandler AddTool(
        string name,
        string description,
        Action<McpSchemaBuilder> schemaConfig,
        Func<JObject, CancellationToken, Task<JObject>> handler,
        Action<JObject> annotationsConfig = null,
        string title = null,
        Action<McpSchemaBuilder> outputSchemaConfig = null)
    {
        var builder = new McpSchemaBuilder();
        schemaConfig?.Invoke(builder);

        JObject annotations = null;
        if (annotationsConfig != null)
        {
            annotations = new JObject();
            annotationsConfig(annotations);
        }

        JObject outputSchema = null;
        if (outputSchemaConfig != null)
        {
            var outBuilder = new McpSchemaBuilder();
            outputSchemaConfig(outBuilder);
            outputSchema = outBuilder.Build();
        }

        _tools[name] = new McpToolDefinition
        {
            Name = name,
            Title = title,
            Description = description,
            InputSchema = builder.Build(),
            OutputSchema = outputSchema,
            Annotations = annotations,
            Handler = async (args, ct) => await handler(args, ct).ConfigureAwait(false)
        };

        return this;
    }

    // ── Resource Registration ─────────────────────────────────────────────

    /// <summary>
    /// Register a static resource. The handler returns the resource contents
    /// as a JArray of {uri, text, mimeType} or {uri, blob, mimeType} objects.
    /// </summary>
    public McpRequestHandler AddResource(
        string uri,
        string name,
        string description,
        Func<CancellationToken, Task<JArray>> handler,
        string mimeType = "application/json",
        Action<JObject> annotationsConfig = null)
    {
        JObject annotations = null;
        if (annotationsConfig != null)
        {
            annotations = new JObject();
            annotationsConfig(annotations);
        }

        _resources[uri] = new McpResourceDefinition
        {
            Uri = uri,
            Name = name,
            Description = description,
            MimeType = mimeType,
            Annotations = annotations,
            Handler = handler
        };

        return this;
    }

    /// <summary>
    /// Register a resource template. The handler receives the resolved URI
    /// and returns the resource contents as a JArray.
    /// </summary>
    public McpRequestHandler AddResourceTemplate(
        string uriTemplate,
        string name,
        string description,
        Func<string, CancellationToken, Task<JArray>> handler,
        string mimeType = "application/json",
        Action<JObject> annotationsConfig = null)
    {
        JObject annotations = null;
        if (annotationsConfig != null)
        {
            annotations = new JObject();
            annotationsConfig(annotations);
        }

        _resourceTemplates.Add(new McpResourceTemplateDefinition
        {
            UriTemplate = uriTemplate,
            Name = name,
            Description = description,
            MimeType = mimeType,
            Annotations = annotations,
            Handler = handler
        });

        return this;
    }

    // ── Prompt Registration ──────────────────────────────────────────────

    /// <summary>
    /// Register a prompt. The handler receives the argument values as a JObject
    /// and returns a JArray of message objects ({role, content: {type, text}}).
    /// </summary>
    public McpRequestHandler AddPrompt(
        string name,
        string description,
        List<McpPromptArgument> arguments,
        Func<JObject, CancellationToken, Task<JArray>> handler)
    {
        _prompts[name] = new McpPromptDefinition
        {
            Name = name,
            Description = description,
            Arguments = arguments ?? new List<McpPromptArgument>(),
            Handler = handler
        };

        return this;
    }

    // ── Main Handler ─────────────────────────────────────────────────────

    /// <summary>
    /// Process a raw JSON-RPC 2.0 request string and return a JSON-RPC response string.
    /// This is the single method that bridges the gap.
    /// </summary>
    public async Task<string> HandleAsync(string body, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(body))
            return SerializeError(null, McpErrorCode.InvalidRequest, "Empty request body");

        JObject request;
        try
        {
            request = JObject.Parse(body);
        }
        catch (JsonException)
        {
            return SerializeError(null, McpErrorCode.ParseError, "Invalid JSON");
        }

        var method = request.Value<string>("method") ?? string.Empty;
        var id = request["id"];

        Log("McpRequestReceived", new { Method = method, HasId = id != null });

        try
        {
            switch (method)
            {
                // Core initialization
                case "initialize":
                    return HandleInitialize(id, request);

                // Notifications — Copilot Studio requires valid JSON-RPC for ALL requests
                case "initialized":
                case "notifications/initialized":
                case "notifications/cancelled":
                case "notifications/roots/list_changed":
                    return SerializeSuccess(id, new JObject());

                // Health check
                case "ping":
                    return SerializeSuccess(id, new JObject());

                // Tools
                case "tools/list":
                    return HandleToolsList(id);

                case "tools/call":
                    return await HandleToolsCallAsync(id, request, cancellationToken).ConfigureAwait(false);

                // Resources
                case "resources/list":
                    return HandleResourcesList(id);

                case "resources/templates/list":
                    return HandleResourceTemplatesList(id);

                case "resources/read":
                    return await HandleResourcesReadAsync(id, request, cancellationToken).ConfigureAwait(false);

                case "resources/subscribe":
                case "resources/unsubscribe":
                    return SerializeSuccess(id, new JObject());

                // Prompts
                case "prompts/list":
                    return HandlePromptsList(id);

                case "prompts/get":
                    return await HandlePromptsGetAsync(id, request, cancellationToken).ConfigureAwait(false);

                // Completions
                case "completion/complete":
                    return SerializeSuccess(id, new JObject
                    {
                        ["completion"] = new JObject
                        {
                            ["values"] = new JArray(),
                            ["total"] = 0,
                            ["hasMore"] = false
                        }
                    });

                // Logging level
                case "logging/setLevel":
                    return SerializeSuccess(id, new JObject());

                default:
                    Log("McpMethodNotFound", new { Method = method });
                    return SerializeError(id, McpErrorCode.MethodNotFound, "Method not found", method);
            }
        }
        catch (McpException ex)
        {
            Log("McpError", new { Method = method, Code = (int)ex.Code, Message = ex.Message });
            return SerializeError(id, ex.Code, ex.Message);
        }
        catch (Exception ex)
        {
            Log("McpError", new { Method = method, Error = ex.Message });
            return SerializeError(id, McpErrorCode.InternalError, ex.Message);
        }
    }

    // ── Protocol Handlers ────────────────────────────────────────────────

    private string HandleInitialize(JToken id, JObject request)
    {
        var clientProtocolVersion = request["params"]?["protocolVersion"]?.ToString()
            ?? _options.ProtocolVersion;

        var capabilities = new JObject();
        if (_options.Capabilities.Tools)
            capabilities["tools"] = new JObject { ["listChanged"] = false };
        if (_options.Capabilities.Resources)
            capabilities["resources"] = new JObject { ["subscribe"] = false, ["listChanged"] = false };
        if (_options.Capabilities.Prompts)
            capabilities["prompts"] = new JObject { ["listChanged"] = false };
        if (_options.Capabilities.Logging)
            capabilities["logging"] = new JObject();
        if (_options.Capabilities.Completions)
            capabilities["completions"] = new JObject();

        var serverInfo = new JObject
        {
            ["name"] = _options.ServerInfo.Name,
            ["version"] = _options.ServerInfo.Version
        };
        if (!string.IsNullOrWhiteSpace(_options.ServerInfo.Title))
            serverInfo["title"] = _options.ServerInfo.Title;
        if (!string.IsNullOrWhiteSpace(_options.ServerInfo.Description))
            serverInfo["description"] = _options.ServerInfo.Description;

        var result = new JObject
        {
            ["protocolVersion"] = clientProtocolVersion,
            ["capabilities"] = capabilities,
            ["serverInfo"] = serverInfo
        };

        if (!string.IsNullOrWhiteSpace(_options.Instructions))
            result["instructions"] = _options.Instructions;

        Log("McpInitialized", new
        {
            Server = _options.ServerInfo.Name,
            Version = _options.ServerInfo.Version,
            ProtocolVersion = clientProtocolVersion
        });

        return SerializeSuccess(id, result);
    }

    private string HandleToolsList(JToken id)
    {
        var toolsArray = new JArray();
        foreach (var tool in _tools.Values)
        {
            var toolObj = new JObject
            {
                ["name"] = tool.Name,
                ["description"] = tool.Description,
                ["inputSchema"] = tool.InputSchema
            };
            if (!string.IsNullOrWhiteSpace(tool.Title))
                toolObj["title"] = tool.Title;
            if (tool.OutputSchema != null)
                toolObj["outputSchema"] = tool.OutputSchema;
            if (tool.Annotations != null && tool.Annotations.Count > 0)
                toolObj["annotations"] = tool.Annotations;
            toolsArray.Add(toolObj);
        }

        Log("McpToolsListed", new { Count = _tools.Count });
        return SerializeSuccess(id, new JObject { ["tools"] = toolsArray });
    }

    private string HandleResourcesList(JToken id)
    {
        var resourcesArray = new JArray();
        foreach (var res in _resources.Values)
        {
            var obj = new JObject
            {
                ["uri"] = res.Uri,
                ["name"] = res.Name
            };
            if (!string.IsNullOrWhiteSpace(res.Description))
                obj["description"] = res.Description;
            if (!string.IsNullOrWhiteSpace(res.MimeType))
                obj["mimeType"] = res.MimeType;
            if (res.Annotations != null && res.Annotations.Count > 0)
                obj["annotations"] = res.Annotations;
            resourcesArray.Add(obj);
        }

        Log("McpResourcesListed", new { Count = _resources.Count });
        return SerializeSuccess(id, new JObject { ["resources"] = resourcesArray });
    }

    private string HandleResourceTemplatesList(JToken id)
    {
        var templatesArray = new JArray();
        foreach (var tmpl in _resourceTemplates)
        {
            var obj = new JObject
            {
                ["uriTemplate"] = tmpl.UriTemplate,
                ["name"] = tmpl.Name
            };
            if (!string.IsNullOrWhiteSpace(tmpl.Description))
                obj["description"] = tmpl.Description;
            if (!string.IsNullOrWhiteSpace(tmpl.MimeType))
                obj["mimeType"] = tmpl.MimeType;
            if (tmpl.Annotations != null && tmpl.Annotations.Count > 0)
                obj["annotations"] = tmpl.Annotations;
            templatesArray.Add(obj);
        }

        Log("McpResourceTemplatesListed", new { Count = _resourceTemplates.Count });
        return SerializeSuccess(id, new JObject { ["resourceTemplates"] = templatesArray });
    }

    private async Task<string> HandleResourcesReadAsync(JToken id, JObject request, CancellationToken ct)
    {
        var paramsObj = request["params"] as JObject;
        var uri = paramsObj?.Value<string>("uri");

        if (string.IsNullOrWhiteSpace(uri))
            return SerializeError(id, McpErrorCode.InvalidParams, "Resource URI is required");

        // 1. Try exact match on registered static resources
        if (_resources.TryGetValue(uri, out var resource))
        {
            Log("McpResourceReadStarted", new { Uri = uri });
            try
            {
                var contents = await resource.Handler(ct).ConfigureAwait(false);
                Log("McpResourceReadCompleted", new { Uri = uri });
                return SerializeSuccess(id, new JObject { ["contents"] = contents });
            }
            catch (Exception ex)
            {
                Log("McpResourceReadError", new { Uri = uri, Error = ex.Message });
                return SerializeError(id, McpErrorCode.InternalError, ex.Message);
            }
        }

        // 2. Try matching against registered resource templates
        foreach (var tmpl in _resourceTemplates)
        {
            if (MatchesUriTemplate(tmpl.UriTemplate, uri))
            {
                Log("McpResourceReadStarted", new { Uri = uri, Template = tmpl.UriTemplate });
                try
                {
                    var contents = await tmpl.Handler(uri, ct).ConfigureAwait(false);
                    Log("McpResourceReadCompleted", new { Uri = uri });
                    return SerializeSuccess(id, new JObject { ["contents"] = contents });
                }
                catch (Exception ex)
                {
                    Log("McpResourceReadError", new { Uri = uri, Error = ex.Message });
                    return SerializeError(id, McpErrorCode.InternalError, ex.Message);
                }
            }
        }

        return SerializeError(id, McpErrorCode.InvalidParams, $"Resource not found: {uri}");
    }

    /// <summary>
    /// Simple URI template matcher. Checks if a concrete URI matches a template
    /// with {param} placeholders (e.g., "data://records/{id}" matches "data://records/123").
    /// </summary>
    private static bool MatchesUriTemplate(string template, string uri)
    {
        // Split both on '/' and compare segments
        var templateParts = template.Split('/');
        var uriParts = uri.Split('/');

        if (templateParts.Length != uriParts.Length) return false;

        for (int i = 0; i < templateParts.Length; i++)
        {
            var seg = templateParts[i];
            if (seg.StartsWith("{") && seg.EndsWith("}")) continue; // wildcard
            if (!string.Equals(seg, uriParts[i], StringComparison.OrdinalIgnoreCase)) return false;
        }
        return true;
    }

    /// <summary>
    /// Extract named parameters from a URI given a template pattern.
    /// E.g., template "data://records/{id}" with uri "data://records/123" returns { "id": "123" }.
    /// </summary>
    public static Dictionary<string, string> ExtractUriParameters(string template, string uri)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        var templateParts = template.Split('/');
        var uriParts = uri.Split('/');

        if (templateParts.Length != uriParts.Length) return result;

        for (int i = 0; i < templateParts.Length; i++)
        {
            var seg = templateParts[i];
            if (seg.StartsWith("{") && seg.EndsWith("}"))
            {
                var paramName = seg.Substring(1, seg.Length - 2);
                result[paramName] = uriParts[i];
            }
        }
        return result;
    }

    private string HandlePromptsList(JToken id)
    {
        var promptsArray = new JArray();
        foreach (var prompt in _prompts.Values)
        {
            var obj = new JObject
            {
                ["name"] = prompt.Name
            };
            if (!string.IsNullOrWhiteSpace(prompt.Description))
                obj["description"] = prompt.Description;

            if (prompt.Arguments.Count > 0)
            {
                var argsArray = new JArray();
                foreach (var arg in prompt.Arguments)
                {
                    var argObj = new JObject { ["name"] = arg.Name };
                    if (!string.IsNullOrWhiteSpace(arg.Description))
                        argObj["description"] = arg.Description;
                    if (arg.Required)
                        argObj["required"] = true;
                    argsArray.Add(argObj);
                }
                obj["arguments"] = argsArray;
            }

            promptsArray.Add(obj);
        }

        Log("McpPromptsListed", new { Count = _prompts.Count });
        return SerializeSuccess(id, new JObject { ["prompts"] = promptsArray });
    }

    private async Task<string> HandlePromptsGetAsync(JToken id, JObject request, CancellationToken ct)
    {
        var paramsObj = request["params"] as JObject;
        var promptName = paramsObj?.Value<string>("name");
        var arguments = paramsObj?["arguments"] as JObject ?? new JObject();

        if (string.IsNullOrWhiteSpace(promptName))
            return SerializeError(id, McpErrorCode.InvalidParams, "Prompt name is required");

        if (!_prompts.TryGetValue(promptName, out var prompt))
            return SerializeError(id, McpErrorCode.InvalidParams, $"Prompt not found: {promptName}");

        Log("McpPromptGetStarted", new { Prompt = promptName });

        try
        {
            var messages = await prompt.Handler(arguments, ct).ConfigureAwait(false);
            Log("McpPromptGetCompleted", new { Prompt = promptName, MessageCount = messages.Count });

            var result = new JObject { ["messages"] = messages };
            if (!string.IsNullOrWhiteSpace(prompt.Description))
                result["description"] = prompt.Description;

            return SerializeSuccess(id, result);
        }
        catch (Exception ex)
        {
            Log("McpPromptGetError", new { Prompt = promptName, Error = ex.Message });
            return SerializeError(id, McpErrorCode.InternalError, ex.Message);
        }
    }

    private async Task<string> HandleToolsCallAsync(JToken id, JObject request, CancellationToken ct)
    {
        var paramsObj = request["params"] as JObject;
        var toolName = paramsObj?.Value<string>("name");
        var arguments = paramsObj?["arguments"] as JObject ?? new JObject();

        if (string.IsNullOrWhiteSpace(toolName))
            return SerializeError(id, McpErrorCode.InvalidParams, "Tool name is required");

        if (!_tools.TryGetValue(toolName, out var tool))
            return SerializeError(id, McpErrorCode.InvalidParams, $"Unknown tool: {toolName}");

        Log("McpToolCallStarted", new { Tool = toolName });

        try
        {
            var result = await tool.Handler(arguments, ct).ConfigureAwait(false);

            JObject callResult;

            // Support pre-formatted MCP tool results with rich content types
            // (image, audio, resource, or mixed content arrays).
            // If the handler returns { "content": [ { "type": "..." } ], ... },
            // pass it through directly instead of wrapping in text.
            if (result is JObject jobj && jobj["content"] is JArray contentArray
                && contentArray.Count > 0 && contentArray[0]?["type"] != null)
            {
                callResult = new JObject
                {
                    ["content"] = contentArray,
                    ["isError"] = jobj.Value<bool?>("isError") ?? false
                };
                if (jobj["structuredContent"] is JObject structured)
                    callResult["structuredContent"] = structured;
            }
            else
            {
                string text;
                if (result is JObject plainObj)
                    text = plainObj.ToString(Newtonsoft.Json.Formatting.Indented);
                else if (result is string s)
                    text = s;
                else if (result == null)
                    text = "{}";
                else
                    text = JsonConvert.SerializeObject(result, Newtonsoft.Json.Formatting.Indented);

                callResult = new JObject
                {
                    ["content"] = new JArray { new JObject { ["type"] = "text", ["text"] = text } },
                    ["isError"] = false
                };
            }

            Log("McpToolCallCompleted", new { Tool = toolName, IsError = callResult.Value<bool>("isError") });
            return SerializeSuccess(id, callResult);
        }
        catch (ArgumentException ex)
        {
            return SerializeSuccess(id, new JObject
            {
                ["content"] = new JArray
                {
                    new JObject { ["type"] = "text", ["text"] = $"Invalid arguments: {ex.Message}" }
                },
                ["isError"] = true
            });
        }
        catch (McpException ex)
        {
            return SerializeSuccess(id, new JObject
            {
                ["content"] = new JArray
                {
                    new JObject { ["type"] = "text", ["text"] = $"Tool error: {ex.Message}" }
                },
                ["isError"] = true
            });
        }
        catch (Exception ex)
        {
            Log("McpToolCallError", new { Tool = toolName, Error = ex.Message });

            return SerializeSuccess(id, new JObject
            {
                ["content"] = new JArray
                {
                    new JObject { ["type"] = "text", ["text"] = $"Tool execution failed: {ex.Message}" }
                },
                ["isError"] = true
            });
        }
    }

    // ── Content Helpers ────────────────────────────────────────────────
    //
    //    Use these to build rich tool results with image, audio, or resource
    //    content. Return McpRequestHandler.ToolResult(...) from your handler
    //    to bypass automatic text wrapping.
    //

    /// <summary>Create a text content item.</summary>
    public static JObject TextContent(string text) =>
        new JObject { ["type"] = "text", ["text"] = text };

    /// <summary>Create an image content item (base64-encoded).</summary>
    public static JObject ImageContent(string base64Data, string mimeType) =>
        new JObject { ["type"] = "image", ["data"] = base64Data, ["mimeType"] = mimeType };

    /// <summary>Create an audio content item (base64-encoded).</summary>
    public static JObject AudioContent(string base64Data, string mimeType) =>
        new JObject { ["type"] = "audio", ["data"] = base64Data, ["mimeType"] = mimeType };

    /// <summary>Create an embedded resource content item.</summary>
    public static JObject ResourceContent(string uri, string text, string mimeType = "text/plain") =>
        new JObject
        {
            ["type"] = "resource",
            ["resource"] = new JObject { ["uri"] = uri, ["text"] = text, ["mimeType"] = mimeType }
        };

    /// <summary>
    /// Build a pre-formatted tool result with mixed content types.
    /// Return this from a tool handler to bypass automatic text wrapping.
    /// </summary>
    public static JObject ToolResult(JArray content, JObject structuredContent = null, bool isError = false)
    {
        var result = new JObject { ["content"] = content, ["isError"] = isError };
        if (structuredContent != null) result["structuredContent"] = structuredContent;
        return result;
    }

    // ── JSON-RPC Serialization ───────────────────────────────────────────

    private string SerializeSuccess(JToken id, JObject result)
    {
        return new JObject
        {
            ["jsonrpc"] = "2.0",
            ["id"] = id,
            ["result"] = result
        }.ToString(Newtonsoft.Json.Formatting.None);
    }

    private string SerializeError(JToken id, McpErrorCode code, string message, string data = null)
    {
        return SerializeError(id, (int)code, message, data);
    }

    private string SerializeError(JToken id, int code, string message, string data = null)
    {
        var error = new JObject
        {
            ["code"] = code,
            ["message"] = message
        };
        if (!string.IsNullOrWhiteSpace(data))
            error["data"] = data;

        return new JObject
        {
            ["jsonrpc"] = "2.0",
            ["id"] = id,
            ["error"] = error
        }.ToString(Newtonsoft.Json.Formatting.None);
    }

    private void Log(string eventName, object data)
    {
        OnLog?.Invoke(eventName, data);
    }
}
