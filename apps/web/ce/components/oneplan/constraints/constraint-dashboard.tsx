/**
 * Flow & Constraints dashboard
 */

import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import { Button } from "@plane/propel/button";
import { API_BASE_URL } from "@plane/constants";
import type { IConstraint } from "@plane/services";
import { OnePlanService } from "@plane/services";
import { useParams } from "react-router";

const service = new OnePlanService(API_BASE_URL);

export const ConstraintDashboard = observer(function ConstraintDashboard() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug ?? "";
  const [constraints, setConstraints] = useState<IConstraint[]>([]);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    if (!slug) return;
    service.getRankedConstraints(slug).then(setConstraints).catch(() => setConstraints([]));
  }, [slug]);

  const add = async () => {
    if (!slug || !newTitle.trim()) return;
    await service.createConstraint(slug, { title: newTitle, status: "identified" });
    setNewTitle("");
    const updated = await service.getRankedConstraints(slug);
    setConstraints(updated);
  };

  return (
    <div className="space-y-4 p-6">
      <h1 className="text-20 font-semibold text-primary">Focus — Constraints</h1>
      <p className="text-13 text-secondary">
        Identify bottlenecks blocking your objectives. Ranked by leverage score.
      </p>

      <div className="flex gap-2">
        <input
          className="flex-1 rounded border border-subtle bg-layer-1 px-3 py-2 text-13"
          placeholder="New constraint…"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
        />
        <Button variant="primary" onClick={add}>
          Add
        </Button>
      </div>

      <ul className="space-y-2">
        {constraints.map((c) => (
          <li key={c.id} className="rounded border border-subtle p-4">
            <div className="flex justify-between">
              <span className="font-medium text-primary">{c.title}</span>
              <span className="text-12 text-secondary">Score: {c.priority_score?.toFixed(1) ?? 0}</span>
            </div>
            <p className="mt-1 text-12 text-tertiary capitalize">{c.status}</p>
          </li>
        ))}
      </ul>
    </div>
  );
});
