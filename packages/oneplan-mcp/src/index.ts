#!/usr/bin/env node
/**
 * OnePlan MCP Server
 * Exposes OnePlan API tools for external AI agents via Model Context Protocol.
 *
 * Env:
 *   ONEPLAN_API_URL - e.g. http://localhost:8000
 *   ONEPLAN_API_KEY - X-Api-Key token (plane_api_*)
 *   ONEPLAN_WORKSPACE_SLUG - default workspace slug
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
