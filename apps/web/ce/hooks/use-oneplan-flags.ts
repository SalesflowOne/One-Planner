/**
 * OnePlan feature flags from instance config
 */

import { useInstance } from "@/hooks/store/use-instance";

export function useOnePlanFlags() {
  const { config } = useInstance();

  const enabled = config?.enable_oneplan_features !== false;
  const aiOperator = enabled && config?.enable_ai_operator !== false;
  const flowConstraints = enabled && config?.enable_flow_constraints !== false;
  const ceoCommand = enabled && config?.enable_ceo_command_mode !== false;
  const llmConfigured = config?.has_llm_configured === true;

  return {
    enabled,
    aiOperator,
    flowConstraints,
    ceoCommand,
    llmConfigured,
    connectors: enabled && aiOperator && config?.enable_pipedream_connectors !== false,
  };
}
