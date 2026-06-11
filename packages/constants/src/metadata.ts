/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

const APP_NAME = process.env.VITE_APP_NAME || "OnePlan";

export const SITE_NAME = `${APP_NAME} | AI-powered execution operating system`;
export const SITE_TITLE = `${APP_NAME} | AI-powered execution operating system`;
export const SITE_DESCRIPTION =
  "OnePlan.one — manage objectives, constraints, flow, and execution with an AI operator built on open-source project management";
export const SITE_KEYWORDS =
  "oneplan, project management, constraints, objectives, AI operator, execution, flow, task management, agile";
export const SITE_URL = process.env.VITE_WEB_BASE_URL || "https://oneplan.one/";
export const TWITTER_USER_NAME = APP_NAME;

// Plane Sites Metadata
export const SPACE_SITE_NAME = `${APP_NAME} Publish | Share boards and roadmaps publicly`;
export const SPACE_SITE_TITLE = `${APP_NAME} Publish | Public boards with one click`;
export const SPACE_SITE_DESCRIPTION = `${APP_NAME} Publish — customer feedback and public roadmaps`;
export const SPACE_SITE_KEYWORDS =
  "project management, customer feedback, roadmaps, constraints, execution";
export const SPACE_SITE_URL = process.env.VITE_SPACE_BASE_URL || SITE_URL;
export const SPACE_TWITTER_USER_NAME = "oneplanone";
