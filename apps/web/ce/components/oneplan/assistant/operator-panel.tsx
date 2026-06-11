/**
 * OnePlan AI Operator — Ask / Plan / Act modes
 */

import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import { Button } from "@plane/propel/button";
import { API_BASE_URL } from "@plane/constants";
import type { TOnePlanMode } from "@plane/services";
import { OnePlanService } from "@plane/services";
import { useTranslation } from "@plane/i18n";
import { useParams } from "react-router";
import { useOnePlanFlags } from "@/plane-web/hooks/use-oneplan-flags";

const service = new OnePlanService(API_BASE_URL);

type TPreview = {
  preview_id: string;
  action: string;
  result: Record<string, unknown>;
};

export const OperatorPanel = observer(function OperatorPanel() {
  const { t } = useTranslation();
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug ?? "";
  const { aiOperator, llmConfigured } = useOnePlanFlags();
  const [mode, setMode] = useState<TOnePlanMode>("ask");
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [previews, setPreviews] = useState<TPreview[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();

  useEffect(() => {
    service.getConfig().catch(() => undefined);
  }, []);

  if (!aiOperator) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-13 text-secondary">
        {t("oneplan.ai_disabled")}
      </div>
    );
  }

  if (!llmConfigured) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-13 text-secondary">
        {t("oneplan.llm_not_configured")}
      </div>
    );
  }

  const send = async () => {
    if (!slug || !message.trim()) return;
    setLoading(true);
    try {
      const data = await service.chat(slug, {
        message,
        mode,
        conversation_id: conversationId,
        dry_run: mode !== "act",
      });
      setResponse(data.response || "");
      setConversationId(data.conversation_id);
      setPreviews(data.previews || []);
      setMessage("");
    } catch {
      setResponse("Error contacting AI operator. Check LLM configuration in God Mode.");
    } finally {
      setLoading(false);
    }
  };

  const approve = async (previewId: string) => {
    if (!slug) return;
    await service.approveAction(slug, previewId);
    setPreviews((p) => p.filter((x) => x.preview_id !== previewId));
    setResponse((r) => r + "\n\n✓ Action approved and executed.");
  };

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-16 font-semibold text-primary">Alfred — AI Operator</h2>
        <div className="flex gap-1">
          {(["ask", "plan", "act"] as TOnePlanMode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`rounded px-2 py-1 text-12 capitalize ${
                mode === m ? "bg-accent-primary text-on-color" : "bg-layer-2 text-secondary"
              }`}
            >
              {m === "ask" ? "Brief" : m === "plan" ? "Blueprint" : "Execute"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto rounded-md border border-subtle bg-layer-1 p-3 text-13 text-primary whitespace-pre-wrap min-h-[200px]">
        {response || "Ask about your workspace, constraints, or priorities…"}
      </div>

      {previews.length > 0 && (
        <div className="space-y-2">
          <p className="text-12 font-medium text-secondary">Pending approvals</p>
          {previews.map((p) => (
            <div key={p.preview_id} className="flex items-center justify-between rounded border border-subtle p-2">
              <span className="text-13">{p.action}</span>
              <Button variant="primary" size="sm" onClick={() => approve(p.preview_id)}>
                Approve
              </Button>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <input
          className="flex-1 rounded border border-subtle bg-layer-1 px-3 py-2 text-13"
          placeholder={
            mode === "ask"
              ? "What is blocking progress?"
              : mode === "plan"
                ? "Create a plan to resolve…"
                : "Execute approved changes…"
          }
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
        />
        <Button variant="primary" onClick={send} loading={loading}>
          Send
        </Button>
      </div>
    </div>
  );
});
