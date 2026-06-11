/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { APIService } from "../api.service";

export type TOnePlanMode = "ask" | "plan" | "act";

export interface IOnePlanChatRequest {
  message: string;
  mode?: TOnePlanMode;
  conversation_id?: string;
  dry_run?: boolean;
}

export interface IConstraint {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority_score: number;
  objective_id?: string;
  pillar_id?: string;
  owner_id?: string;
  linked_issue_ids?: string[];
}

export class OnePlanService extends APIService {
  constructor(baseURL: string) {
    super(baseURL);
  }

  async getConfig() {
    return this.get("/api/oneplan/config/").then((r) => r?.data);
  }

  async chat(workspaceSlug: string, data: IOnePlanChatRequest) {
    return this.post(`/api/oneplan/workspaces/${workspaceSlug}/chat/`, data).then((r) => r?.data);
  }

  async approveAction(workspaceSlug: string, previewId: string) {
    return this.post(`/api/oneplan/workspaces/${workspaceSlug}/actions/approve/`, {
      preview_id: previewId,
    }).then((r) => r?.data);
  }

  async getConstraints(workspaceSlug: string, status?: string) {
    const params = status ? `?status=${status}` : "";
    return this.get(`/api/oneplan/workspaces/${workspaceSlug}/constraints/${params}`).then((r) => r?.data);
  }

  async createConstraint(workspaceSlug: string, data: Partial<IConstraint>) {
    return this.post(`/api/oneplan/workspaces/${workspaceSlug}/constraints/`, data).then((r) => r?.data);
  }

  async getRankedConstraints(workspaceSlug: string) {
    return this.get(`/api/oneplan/workspaces/${workspaceSlug}/constraints/rank/`).then((r) => r?.data);
  }

  async getCommandCenter(workspaceSlug: string) {
    return this.get(`/api/oneplan/workspaces/${workspaceSlug}/command/`).then((r) => r?.data);
  }

  async getObjectives(workspaceSlug: string) {
    return this.get(`/api/oneplan/workspaces/${workspaceSlug}/objectives/`).then((r) => r?.data);
  }

  async getActionLogs(workspaceSlug: string) {
    return this.get(`/api/oneplan/workspaces/${workspaceSlug}/actions/logs/`).then((r) => r?.data);
  }

  async getConnectorsStatus() {
    return this.get("/api/oneplan/connectors/status/").then((r) => r?.data);
  }

  async getConnectorApps(workspaceSlug: string) {
    return this.get(`/api/oneplan/workspaces/${workspaceSlug}/connectors/apps/`).then((r) => r?.data);
  }

  async runConnector(
    workspaceSlug: string,
    data: { app_slug: string; tool_name: string; arguments?: Record<string, unknown> }
  ) {
    return this.post(`/api/oneplan/workspaces/${workspaceSlug}/connectors/run/`, data).then((r) => r?.data);
  }
}
