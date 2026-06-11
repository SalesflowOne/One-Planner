/**
 * Pipedream MCP connectors — browse and connect external apps
 */

import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import { ExternalLink } from "lucide-react";
import { useParams } from "react-router";
import { API_BASE_URL } from "@plane/constants";
import { OnePlanService } from "@plane/services";
import { useOnePlanFlags } from "@/plane-web/hooks/use-oneplan-flags";

const service = new OnePlanService(API_BASE_URL);

type TConnectorApp = { slug: string; name: string };

export const ConnectorsPanel = observer(function ConnectorsPanel() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug ?? "";
  const { connectors } = useOnePlanFlags();
  const [apps, setApps] = useState<TConnectorApp[]>([]);
  const [configured, setConfigured] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!connectors) {
      setLoading(false);
      return;
    }
    Promise.all([service.getConnectorsStatus(), slug ? service.getConnectorApps(slug) : Promise.resolve({ apps: [] })])
      .then(([status, data]) => {
        setConfigured(status?.pipedream_configured === true);
        setApps(data?.apps ?? []);
        return undefined;
      })
      .finally(() => setLoading(false));
  }, [connectors, slug]);

  if (!connectors) {
    return <p className="p-4 text-13 text-secondary">Connectors require OnePlan AI operator to be enabled.</p>;
  }

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div>
        <h2 className="text-16 font-semibold text-primary">Pipedream Connectors</h2>
        <p className="text-13 text-secondary">
          Connect Slack, GitHub, Notion, and 3,000+ apps via Pipedream MCP. Alfred can use connected tools in chat.
        </p>
      </div>

      {!configured && (
        <div className="rounded-md border border-subtle bg-layer-2 p-3 text-13 text-secondary">
          Pipedream credentials are not configured on this instance. Add PIPEDREAM_CLIENT_ID, PIPEDREAM_CLIENT_SECRET,
          and PIPEDREAM_PROJECT_ID in God Mode / deployment env.
        </div>
      )}

      {loading ? (
        <p className="text-13 text-secondary">Loading connectors…</p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {apps.map((app) => (
            <a
              key={app.slug}
              href={`https://mcp.pipedream.com/app/${app.slug}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between rounded-md border border-subtle bg-layer-1 p-3 text-13 hover:bg-layer-2"
            >
              <span className="font-medium text-primary">{app.name}</span>
              <ExternalLink className="size-3.5 text-tertiary" />
            </a>
          ))}
        </div>
      )}
    </div>
  );
});
