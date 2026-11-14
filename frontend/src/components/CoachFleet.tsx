import { useQuery } from "@tanstack/react-query";
import { Bot, Gauge, MessageSquare, Users } from "lucide-react";
import { Badge, Card, CardHeader, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { cn, timeAgo } from "@/lib/utils";

/* The admin's view of Edify Coach: every student's coach, and Maritime's own view of the machines (one per
   student): who is active, how much they talk to it, what its AI costs, and the limits each one runs under. */

const dollars = (cents: number) => `$${(cents / 100).toFixed(cents < 100 ? 3 : 2)}`;

function Spark({ values }: { values: number[] }) {
  const max = Math.max(1, ...values);
  return (
    <span className="inline-flex h-5 items-end gap-px" aria-label={`Messages over 14 days: ${values.join(", ")}`}>
      {values.map((v, i) => <span key={i} className={cn("w-1 rounded-sm", v ? "bg-fg" : "bg-line-strong")} style={{ height: `${Math.max(12, (100 * v) / max)}%` }} />)}
    </span>
  );
}

export function CoachFleet() {
  const { data: f, error } = useQuery({ queryKey: ["admin-coaches"], queryFn: api.adminCoaches, refetchInterval: 60_000 });
  if (error && !f) return null;
  if (!f) return <Skeleton className="h-40" />;
  const where = f.mode === "maritime" ? "One Maritime machine per student" : f.mode === "local" ? "Running on this computer until Maritime has a card" : "Off";
  const m = f.maritime;

  return (
    <Card>
      <CardHeader title="Edify Coach fleet" icon={<Bot className="h-4 w-4" />} subtitle={where}
        action={<Badge tone={f.mode === "maritime" ? "accent" : "neutral"}>{f.mode === "maritime" ? `Maritime · ${f.tier}` : f.mode ?? "off"}</Badge>} />
      <div className="grid gap-3 px-5 pt-4 sm:grid-cols-4">
        {[
          { icon: Users, label: "Students with a coach", value: f.coaches.length },
          { icon: Users, label: "On Maritime (7-day active)", value: m ? `${m.total} (${m.active_7d})` : "—" },
          { icon: MessageSquare, label: "Messages to coaches", value: m ? m.messages : "—" },
          { icon: Gauge, label: "Limits per student", value: `${dollars(f.policy.llm_spend_cap_cents_per_month)} AI · ${f.policy.wakes_per_hour} wakes/h` },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="rounded-xl border border-line p-3">
            <div className="flex items-center gap-1.5 text-[12px] text-muted"><Icon className="h-3.5 w-3.5" />{label}</div>
            <div className="mt-1 text-[17px] font-semibold tabular-nums">{value}</div>
          </div>
        ))}
      </div>
      {f.maritime_error && <p className="px-5 pt-3 text-[13px] text-warn">Maritime: {f.maritime_error}</p>}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full whitespace-nowrap text-[13px]">
          <thead className="text-left text-xs text-muted">
            <tr>{["Student", "Where", "Machine", "Lectures", "Plans", "Maritime: 14 days", "AI (30 d)", "Last planned"].map((h) => <th key={h} className="px-5 py-2 font-medium">{h}</th>)}</tr>
          </thead>
          <tbody>
            {f.coaches.map((c) => {
              const mu = m?.users.find((u) => u.external_id === `edify_${c.user_id}`);
              return (
                <tr key={c.user_id} className="border-t border-line">
                  <td className="px-5 py-2 font-medium">{c.name}</td>
                  <td className="px-5 py-2">{c.mode === "maritime" ? "Maritime" : "This PC"}</td>
                  <td className="px-5 py-2 text-muted">{mu?.agent_status.join(", ") || c.status}</td>
                  <td className="px-5 py-2 tabular-nums">{c.lectures}</td>
                  <td className="px-5 py-2 tabular-nums">{c.reviews}</td>
                  <td className="px-5 py-2">{mu ? <Spark values={mu.activity_14d} /> : <span className="text-muted">—</span>}</td>
                  <td className="px-5 py-2 tabular-nums">{mu ? dollars(mu.ai_cents_30d) : "—"}</td>
                  <td className="px-5 py-2 text-muted">{c.synced_at ? timeAgo(c.synced_at) : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!f.coaches.length && <p className="px-5 py-4 text-sm text-muted">No student has turned on their coach yet.</p>}
      </div>
    </Card>
  );
}
