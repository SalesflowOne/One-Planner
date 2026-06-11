/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { layout, route } from "@react-router/dev/routes";
import type { RouteConfigEntry } from "@react-router/dev/routes";

/**
 * OnePlan extended routes — deep-merged into core workspace projects layout
 */
export const extendedRoutes: RouteConfigEntry[] = [
  layout("./(all)/layout.tsx", [
    layout("./(all)/[workspaceSlug]/layout.tsx", [
      layout("./(all)/[workspaceSlug]/(projects)/layout.tsx", [
        route(":workspaceSlug/oneplan/command", "./(all)/[workspaceSlug]/(projects)/oneplan/command/page.tsx"),
        route(":workspaceSlug/oneplan/focus", "./(all)/[workspaceSlug]/(projects)/oneplan/focus/page.tsx"),
        route(":workspaceSlug/oneplan/assistant", "./(all)/[workspaceSlug]/(projects)/oneplan/assistant/page.tsx"),
      ]),
    ]),
  ]),
];
