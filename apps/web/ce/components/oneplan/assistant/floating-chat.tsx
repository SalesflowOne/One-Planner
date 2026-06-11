/**
 * Floating Alfred chat launcher — always visible when AI operator is enabled
 */

import { observer } from "mobx-react";
import { MessageSquare } from "lucide-react";
import { Link, useParams, useLocation } from "react-router";
import { useTranslation } from "@plane/i18n";
import { cn } from "@plane/utils";
import { useOnePlanFlags } from "@/plane-web/hooks/use-oneplan-flags";

export const AlfredFloatingChat = observer(function AlfredFloatingChat() {
  const { workspaceSlug } = useParams();
  const { pathname } = useLocation();
  const { t } = useTranslation();
  const { aiOperator } = useOnePlanFlags();

  const slug = workspaceSlug?.toString() ?? "";
  const assistantPath = `/${slug}/oneplan/assistant`;
  const isOnAssistant = pathname.includes("/oneplan/assistant");

  if (!aiOperator || !slug || isOnAssistant) return null;

  return (
    <Link
      to={assistantPath}
      className={cn(
        "fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full border border-subtle bg-accent-primary px-4 py-2.5 text-13 font-medium text-on-color shadow-lg transition-transform hover:scale-105"
      )}
      aria-label={t("oneplan.assistant")}
    >
      <MessageSquare className="size-4" />
      <span>{t("oneplan.assistant")}</span>
    </Link>
  );
});
