#!/usr/bin/env node
/**
 * OnePlan MCP Server
 * Exposes OnePlan API tools for external AI agents via Model Context Protocol.
 *
 * Env:
 *   ONEPLAN_API_URL - e.g. http://localhost:8000
 *   ONEPLAN_API_KEY - X-Api-Key token (plane_api_*)
 *   ONEPLAN_WORKSPACE_SLUG - default workspace slug
 *   PIPEDREAM_CLIENT_ID / PIPEDREAM_CLIENT_SECRET / PIPEDREAM_PROJECT_ID - optional Pipedream MCP
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const API_URL = process.env.ONEPLAN_API_URL || "http://localhost:8000";
const API_KEY = process.env.ONEPLAN_API_KEY || "";
const WORKSPACE_SLUG = process.env.ONEPLAN_WORKSPACE_SLUG || "";
const PIPEDREAM_MCP_URL = process.env.PIPEDREAM_MCP_URL || "https://remote.mcp.pipedream.net/v3";
const PIPEDREAM_CLIENT_ID = process.env.PIPEDREAM_CLIENT_ID || "";
const PIPEDREAM_CLIENT_SECRET = process.env.PIPEDREAM_CLIENT_SECRET || "";
const PIPEDREAM_PROJECT_ID = process.env.PIPEDREAM_PROJECT_ID || "";
const PIPEDREAM_ENVIRONMENT = process.env.PIPEDREAM_ENVIRONMENT || "production";
const EXTERNAL_USER_ID = process.env.PIPEDREAM_EXTERNAL_USER_ID || "oneplan-mcp";

async function getPipedreamToken(): Promise<string | null> {
  if (!PIPEDREAM_CLIENT_ID || !PIPEDREAM_CLIENT_SECRET) return null;
  const res = await fetch("https://api.pipedream.com/v1/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "client_credentials",
      client_id: PIPEDREAM_CLIENT_ID,
      client_secret: PIPEDREAM_CLIENT_SECRET,
    }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access_token?: string };
  return data.access_token ?? null;
}

async function pipedreamMcpCall(appSlug: string, method: string, params: Record<string, unknown> = {}) {
  const token = await getPipedreamToken();
  if (!token || !PIPEDREAM_PROJECT_ID) throw new Error("Pipedream MCP not configured");
  const res = await fetch(PIPEDREAM_MCP_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      "x-pd-project-id": PIPEDREAM_PROJECT_ID,
      "x-pd-environment": PIPEDREAM_ENVIRONMENT,
      "x-pd-external-user-id": EXTERNAL_USER_ID,
      "x-pd-app-slug": appSlug,
    },
    body: JSON.stringify({ jsonrpc: "2.0", id: "1", method, params }),
  });
  if (!res.ok) throw new Error(`Pipedream MCP ${res.status}`);
  const data = (await res.json()) as { result?: unknown; error?: unknown };
  if (data.error) throw new Error(JSON.stringify(data.error));
  return data.result;
}

async function apiRequest(path: string, method = "GET", body?: unknown) {
  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": API_KEY,
    },
  };
  if (body && method !== "GET") {
    init.body = JSON.stringify(body);
  }
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

const TOOLS = [
  { name: "list_workspaces", description: "List workspaces (via user profile)", inputSchema: { type: "object", properties: {} } },
  { name: "summarize_workspace", description: "Get workspace summary", inputSchema: { type: "object", properties: { workspace_slug: { type: "string" } } } },
  { name: "list_constraints", description: "List ranked constraints", inputSchema: { type: "object", properties: { workspace_slug: { type: "string" } } } },
  { name: "search_tasks", description: "Search work items", inputSchema: { type: "object", properties: { workspace_slug: { type: "string" }, query: { type: "string" } } } },
  { name: "create_task", description: "Create work item (dry-run by default)", inputSchema: { type: "object", properties: { workspace_slug: { type: "string" }, tool: { type: "string" }, arguments: { type: "object" }, dry_run: { type: "boolean" } } } },
  { name: "execute_tool", description: "Execute any OnePlan tool", inputSchema: { type: "object", properties: { workspace_slug: { type: "string" }, tool: { type: "string" }, arguments: { type: "object" }, dry_run: { type: "boolean" } }, required: ["tool"] } },
  { name: "list_pipedream_tools", description: "List Pipedream MCP tools for an app", inputSchema: { type: "object", properties: { app_slug: { type: "string" } }, required: ["app_slug"] } },
  { name: "run_pipedream_tool", description: "Run a Pipedream MCP connector tool", inputSchema: { type: "object", properties: { app_slug: { type: "string" }, tool_name: { type: "string" }, arguments: { type: "object" } }, required: ["app_slug", "tool_name"] } },
];

const server = new Server({ name: "oneplan", version: "0.1.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const slug = (args?.workspace_slug as string) || WORKSPACE_SLUG;
  if (!slug) {
    return { content: [{ type: "text", text: "workspace_slug required" }], isError: true };
  }

  try {
    let result: unknown;
    switch (name) {
      case "summarize_workspace":
        result = await apiRequest(`/api/v1/workspaces/${slug}/summary/`);
        break;
      case "list_constraints":
        result = await apiRequest(`/api/v1/workspaces/${slug}/constraints/`);
        break;
      case "execute_tool":
      case "create_task":
      case "search_tasks":
        result = await apiRequest(`/api/v1/workspaces/${slug}/tools/execute/`, "POST", {
          tool: name === "execute_tool" ? args?.tool : name,
          arguments: args?.arguments || { query: args?.query },
          dry_run: args?.dry_run !== false,
        });
        break;
      case "list_workspaces":
        result = await apiRequest("/api/v1/users/me/workspaces/");
        break;
      case "list_pipedream_tools":
        result = await pipedreamMcpCall(args?.app_slug as string, "tools/list");
        break;
      case "run_pipedream_tool":
        result = await pipedreamMcpCall(args?.app_slug as string, "tools/call", {
          name: args?.tool_name,
          arguments: args?.arguments || {},
        });
        break;
      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  } catch (e) {
    return { content: [{ type: "text", text: String(e) }], isError: true };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
