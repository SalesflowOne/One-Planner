/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { API_BASE_URL } from "@plane/constants";
import { OnePlanService } from "@plane/services";

export const onePlanService = new OnePlanService(API_BASE_URL);
