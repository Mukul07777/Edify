import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, BookOpenCheck, Bot, Check, ChevronDown, GitBranch, Moon, RefreshCw, Send, Sparkles, Target, Timer } from "lucide-react";
import { Link } from "react-router-dom";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";
import { Badge, Card, CardHeader, Skeleton } from "@/components/ui/primitives";
import { api, ApiError } from "@/lib/api";
import type { CoachPack, CoachPlanItem, CoachView } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

/* Edify Coach: the student's own study agent, on its own Maritime machine. It remembers them across weeks, writes a
   revision pack after each lecture, re-plans every night, and answers questions. Hidden when the server has no coach. */

const KIND_ICON: Record<CoachPlanItem["kind"], typeof Target> = { root: GitBranch, revise: BookOpenCheck, weak: Target, mock: Timer, start: Sparkles };
const failed = (fallback: string) => (e: unknown) => toast.error(e instanceof ApiError ? e.message : fallback);

function PlanItem({ item, onDone, busy }: { item: CoachPlanItem; onDone?: () => void; busy?: boolean }) {
  const Icon = KIND_ICON[item.kind] ?? Sparkles;
  return (
    <li className="flex items-start gap-3 rounded-xl border border-line bg-bg-soft/60 p-3">
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-panel text-fg shadow-sm"><Icon className="h-4 w-4" /></span>
      <span className="min-w-0 flex-1">
        <span className="block text-[14px] font-medium leading-snug">{item.title}</span>
        <span className="mt-0.5 block text-[12.5px] text-muted">{item.why} · {item.minutes} min</span>
      </span>
      {item.kind === "root" && item.trace_id && (
        <Link to={`/app/roots?trace=${item.trace_id}`}><Button size="sm" variant="primary">Fix it <ArrowRight className="h-3.5 w-3.5" /></Button></Link>
      )}
      {onDone && (
        <Button size="sm" variant="secondary" onClick={onDone} loading={busy} aria-label={`Mark ${item.title} as revised`}>
          <Check className="h-3.5 w-3.5" /> Done
        </Button>
      )}
    </li>
  );
}

function Pack({ pack }: { pack: CoachPack }) {
  const [open, setOpen] = useState(false);
  // a pack saved by an older coach, or an AI reply missing a field, still opens
  const points = pack.key_points ?? [], formulas = pack.formulas ?? [], practice = pack.practice ?? [], again = pack.revise_on ?? [];
  return (
    <div className="rounded-xl border border-line">
      <button onClick={() => setOpen(!open)} aria-expanded={open} className="flex w-full items-center gap-3 p-3 text-left">
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[14px] font-medium">{pack.title}</span>
          <span className="block truncate text-[12.5px] text-muted">{pack.headline}</span>
        </span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="space-y-3 border-t border-line p-3 text-[13.5px]">
          <ul className="space-y-1.5">{points.map((k) => <li key={k} className="flex gap-2"><span className="mt-[0.55em] h-1 w-1 shrink-0 rounded-full bg-fg" />{k}</li>)}</ul>
          {formulas.length > 0 && <div className="rounded-lg bg-bg-soft p-2.5 font-mono text-[12.5px]">{formulas.join("   ·   ")}</div>}
          {pack.link && <p className="text-muted">{pack.link}</p>}
          {practice.length > 0 && (
            <ol className="space-y-2">
              {practice.map((p, i) => (
                <li key={p.q}>
                  <details>
                    <summary className="cursor-pointer">{i + 1}. {p.q}</summary>
                    <div className="mt-1 pl-4 text-muted"><Markdown>{String(p.answer ?? "")}</Markdown></div>
                  </details>
                </li>
              ))}
            </ol>
          )}
          {again.length > 0 && <p className="text-[12px] text-muted">Revise again on {again.map((d) => new Date(d).toLocaleDateString(undefined, { day: "numeric", month: "short" })).join(", ")}</p>}
        </div>
      )}
    </div>
  );
}

export function CoachCard() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["coach"], queryFn: api.coach, staleTime: 60_000 });
  const put = (v: CoachView) => qc.setQueryData(["coach"], v);
  const enable = useMutation({ mutationFn: api.coachEnable, onSuccess: put, onError: failed("Couldn't start your coach") });
  const refresh = useMutation({ mutationFn: api.coachRefresh, onSuccess: put, onError: failed("Your coach couldn't plan right now") });
  const revised = useMutation({ mutationFn: api.coachRevised, onSuccess: put, onError: failed("Couldn't tell your coach") });
  const sample = useMutation({ mutationFn: api.coachSample, onSuccess: put, onError: failed("Your coach couldn't take the sample lecture") });
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const ask = useMutation({
    mutationFn: api.coachAsk,
    onSuccess: (r) => { setAnswer(r.answer); setQuestion(""); },
    onError: failed("Your coach couldn't answer right now"),
  });

  if (!data) return null;
  if (!data.available) return null;
  const maritime = data.on_maritime ? <Badge><Bot className="h-3 w-3" /> On Maritime</Badge>
    : data.maritime_user ? <Badge title="You're registered on Maritime with your own limits. Your coach moves there once Edify's Maritime billing is on."><Bot className="h-3 w-3" /> Limits on Maritime</Badge> : null;

  if (!data.enabled) {
    return (
      <Card className="overflow-hidden">
        <div className="flex flex-col gap-5 p-6 sm:flex-row sm:items-center">
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-fg text-bg"><Bot className="h-6 w-6" /></span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2"><h3 className="text-[17px] font-semibold">Your own study coach</h3>{maritime}</div>
            <p className="mt-1 text-[13.5px] leading-relaxed text-muted">
              An AI coach that is yours alone. It remembers every lecture you finish, writes a revision pack for each, and plans
              your next day every night from your weak spots and mock tests.
            </p>
          </div>
          <Button variant="primary" onClick={() => enable.mutate()} loading={enable.isPending}>Turn on my coach</Button>
        </div>
      </Card>
    );
  }

  const { plan, packs = [], due_today = [] } = data.state;
  const dueIds = new Set(due_today.map((d) => d.lecture_id));
  const submit = (e: FormEvent) => { e.preventDefault(); if (question.trim().length > 1) ask.mutate(question.trim()); };

  return (
    <Card>
      <CardHeader title="Edify Coach" icon={<Bot className="h-4 w-4" />}
        subtitle={data.synced_at ? `Planned ${timeAgo(data.synced_at)} · re-plans every night at 9:30 pm` : "Getting to know you"}
        action={<div className="flex items-center gap-2">{maritime}
          <Button size="icon-sm" variant="ghost" onClick={() => refresh.mutate()} loading={refresh.isPending} aria-label="Re-plan now" title="Re-plan now">
            <RefreshCw className="h-4 w-4" />
          </Button></div>} />
      <div className="grid gap-6 px-5 pb-5 pt-4 lg:grid-cols-[1.3fr_1fr]">
        <div>
          {data.status === "starting" && !plan && (
            <div className="rounded-xl border border-dashed border-line-strong p-4 text-[13.5px] text-muted">
              {data.error ?? "Your coach is starting on its own machine."}
              <Button size="sm" variant="secondary" className="mt-3" onClick={() => refresh.mutate()} loading={refresh.isPending}>Check again</Button>
            </div>
          )}
          {data.status === "failed" && <p className="text-[13.5px] text-bad">{data.error}</p>}
          {plan ? (
            <>
              <div className="flex items-start gap-2">
                <Moon className="mt-1 h-4 w-4 shrink-0 text-muted" />
                <p className="text-[15px] font-medium leading-snug">{plan.headline}</p>
              </div>
              <ul className="mt-4 space-y-2">
                {(plan.items ?? []).map((it) => (
                  <PlanItem key={it.title} item={it} busy={revised.isPending && revised.variables === it.lecture_id}
                    onDone={it.kind === "revise" && it.lecture_id && dueIds.has(it.lecture_id) ? () => revised.mutate(it.lecture_id!) : undefined} />
                ))}
              </ul>
              {(plan.nudges ?? []).length > 0 && (
                <ul className="mt-4 space-y-1.5 text-[13px] text-fg-soft">
                  {plan.nudges.map((n) => <li key={n} className="flex gap-2"><Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red" />{n}</li>)}
                </ul>
              )}
            </>
          ) : data.status === "ready" ? <Skeleton className="h-40" /> : null}
        </div>

        <div className="space-y-4">
          <div>
            <div className="caps mb-2 text-[11px] font-medium text-muted">Revision packs</div>
            {packs.length ? <div className="space-y-2">{packs.slice(0, 3).map((p) => <Pack key={p.lecture_id} pack={p} />)}</div>
              : (
                <div className="rounded-xl border border-dashed border-line-strong p-3">
                  <p className="text-[13px] text-muted">Finish a lecture and your coach writes its revision pack here.</p>
                  <Button size="sm" variant="secondary" className="mt-2.5" onClick={() => sample.mutate()} loading={sample.isPending}>
                    <Sparkles className="h-3.5 w-3.5" /> Try it with a sample lecture
                  </Button>
                </div>
              )}
          </div>
          <form onSubmit={submit}>
            <label htmlFor="coach-ask" className="caps mb-2 block text-[11px] font-medium text-muted">Ask your coach</label>
            <div className="flex items-center gap-1 rounded-full border border-line-strong bg-panel p-1 pl-4 focus-within:border-fg">
              <input id="coach-ask" value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={1500}
                placeholder="What should I fix before Sunday's mock?" className="min-w-0 flex-1 bg-transparent text-[14px] outline-none placeholder:text-muted/80" />
              <Button type="submit" size="icon-sm" variant="primary" loading={ask.isPending} aria-label="Ask"><Send className="h-3.5 w-3.5" /></Button>
            </div>
          </form>
          {answer && <div className="rounded-xl bg-bg-soft p-3 text-[13.5px]"><Markdown>{answer}</Markdown></div>}
        </div>
      </div>
    </Card>
  );
}
