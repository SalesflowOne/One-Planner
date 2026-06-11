/**
 * OnePlan Command Center — executive dashboard
 */

import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import { API_BASE_URL } from "@plane/constants";
import { OnePlanService } from "@plane/services";
import { useParams } from "react-router";

const service = new OnePlanService(API_BASE_URL);

type TCommandData = {
  top_constraints?: Array<{ id: string; title: string; status: string; priority_score: number }>;
  overdue_tasks?: Array<{ id: string; name: string; target_date: string }>;
  stuck_tasks?: Array<{ id: string; name: string }>;
  top_constraints_daily?: unknown[];
  overdue_tasks_daily?: unknown[];
  attention_summary?: string;
};

export const CommandCenter = observer(function CommandCenter() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug ?? "";
  const [data, setData] = useState<TCommandData | null>(null);

  useEffect(() => {
    if (!slug) return;
    service.getCommandCenter(slug).then(setData).catch(() => setData(null));
  }, [slug]);

  if (!data) {
    return <div className="p-6 text-secondary">Loading command center…</div>;
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-20 font-semibold text-primary">Command Center</h1>
        <p className="text-13 text-secondary">{data.attention_summary}</p>
      </div>

      <section>
        <h2 className="mb-2 text-14 font-medium text-primary">Top constraints</h2>
        <ul className="space-y-2">
          {(data.top_constraints || []).map((c) => (
            <li key={c.id} className="flex justify-between rounded border border-subtle p-3 text-13">
              <span>{c.title}</span>
              <span className="text-secondary">{c.priority_score.toFixed(1)} · {c.status}</span>
            </li>
          ))}
          {(data.top_constraints || []).length === 0 && (
            <li className="text-13 text-tertiary">No active constraints. Add one in Focus.</li>
          )}
        </ul>
      </section>

      <section>
        <h2 className="mb-2 text-14 font-medium text-primary">Overdue tasks</h2>
        <ul className="space-y-1">
          {(data.overdue_tasks || []).map((t) => (
            <li key={t.id} className="text-13 text-secondary">
              {t.name}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-2 text-14 font-medium text-primary">Stuck tasks</h2>
        <ul className="space-y-1">
          {(data.stuck_tasks || []).map((t) => (
            <li key={t.id} className="text-13 text-secondary">
              {t.name}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
});
