import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, Check, CircleHelp, GitBranch, Search, Sparkles, Target, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { PageHeader } from "@/components/common";
import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";
import { Badge, Card, CardHeader, EmptyState, Input, Skeleton } from "@/components/ui/primitives";
import { api, ApiError } from "@/lib/api";
import type { GapCheck, GapLink, GapTrace } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

/* Root cause: a topic that won't make sense, traced back through the earlier chapters it rests on. The student
   answers one quick question per link; the deepest one they miss is the real gap, fixed with a five-minute lesson. */

const failed = (fallback: string) => (e: unknown) => toast.error(e instanceof ApiError ? e.message : fallback);
const where = (l: GapLink) => (l.cls ? `Class ${l.cls}` : "Your course") + ` · ${l.subject}`;
const STATUS: Record<GapTrace["status"], { label: string; tone: "neutral" | "warn" | "ok" | "accent" }> = {
  checking: { label: "Checking", tone: "neutral" }, found: { label: "Root found", tone: "warn" },
  clear: { label: "Foundations hold", tone: "ok" }, fixed: { label: "Fixed", tone: "ok" },
};

function Options({ check, value, onPick, locked }: { check: GapCheck; value: number | null | undefined; onPick?: (i: number) => void; locked?: boolean }) {
  return (
    <div className="mt-3 grid gap-2 sm:grid-cols-2">
      {check.options.map((o, i) => {
        const right = locked && check.answer === i;
        const wrongPick = locked && value === i && check.answer !== i;
        return (
          <button key={i} type="button" disabled={locked} onClick={() => onPick?.(i)} aria-pressed={value === i}
            className={cn("rounded-xl border px-3 py-2.5 text-left text-[13.5px] transition",
              !locked && (value === i ? "border-fg bg-fg text-bg" : "border-line-strong bg-panel hover:border-fg"),
              right && "border-ok bg-ok/10", wrongPick && "border-bad bg-bad/10", locked && !right && !wrongPick && "border-line opacity-70")}>
            <span className="mr-2 font-semibold">{"ABCD"[i]}.</span><Markdown className="inline [&_p]:inline">{o}</Markdown>
          </button>
        );
      })}
    </div>
  );
}

function Chain({ trace }: { trace: GapTrace }) {
  const qc = useQueryClient();
  const [picks, setPicks] = useState<(number | null)[]>(() => trace.chain.map(() => null));
  const put = (t: GapTrace) => { qc.setQueryData(["gap", t.id], t); qc.invalidateQueries({ queryKey: ["gaps"] }); };
  const submit = useMutation({ mutationFn: () => api.gapAnswers(trace.id, picks), onSuccess: put, onError: failed("Couldn't check your answers") });
  const lesson = useMutation({ mutationFn: () => api.gapLesson(trace.id), onSuccess: put, onError: failed("Couldn't write the lesson right now") });
  const [pick, setPick] = useState<number | null>(null);
  const recheck = useMutation({ mutationFn: (c: number) => api.gapCheck(trace.id, c), onSuccess: put, onError: failed("Couldn't check that") });
  const checking = trace.status === "checking";
  const root = trace.root !== null ? trace.chain[trace.root] : null;

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-fg text-bg"><Target className="h-5 w-5" /></span>
          <div className="min-w-0">
            <div className="text-[12px] text-muted">You're stuck on</div>
            <div className="truncate text-[17px] font-semibold">{trace.title}</div>
          </div>
          <Badge tone={STATUS[trace.status].tone} className="ml-auto">{STATUS[trace.status].label}</Badge>
        </div>
        {checking && <p className="mt-3 text-[13.5px] text-muted">It rests on these earlier ideas. Answer one quick question for each: the deepest one you miss is your real gap.</p>}
      </Card>

      {trace.chain.map((l, i) => (
        <div key={l.chapter_id}>
          <div className="flex justify-center py-1 text-muted"><ArrowDown className="h-4 w-4" /></div>
          <Card className={cn("p-5", trace.root === i && "ring-2 ring-warn")}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{where(l)}</Badge>
              <span className="text-[13px] text-muted">{l.name}</span>
              {l.result === "right" && <Badge tone="ok"><Check className="h-3 w-3" /> You have this</Badge>}
              {l.result === "wrong" && <Badge tone={trace.root === i ? "warn" : "bad"}><X className="h-3 w-3" /> {trace.root === i ? "Root gap" : "Shaky"}</Badge>}
            </div>
            <div className="mt-2 text-[15px] font-semibold">{l.idea}</div>
            {l.why && <p className="mt-0.5 text-[13px] text-muted">{l.why}</p>}
            <div className="mt-4 flex gap-2 text-[14px]"><CircleHelp className="mt-0.5 h-4 w-4 shrink-0 text-muted" /><Markdown>{l.check.q}</Markdown></div>
            <Options check={l.check} value={checking ? picks[i] : l.choice} locked={!checking}
              onPick={(c) => setPicks((p) => p.map((v, j) => (j === i ? c : v)))} />
            {!checking && l.check.explain && <p className="mt-2 text-[12.5px] text-muted">{l.check.explain}</p>}
          </Card>
        </div>
      ))}

      {checking && (
        <div className="flex flex-wrap items-center justify-end gap-3">
          <span className="text-[13px] text-muted">{picks.filter((p) => p !== null).length} of {picks.length} answered (a skip counts as not known yet)</span>
          <Button variant="primary" onClick={() => submit.mutate()} loading={submit.isPending}>Find my root gap</Button>
        </div>
      )}

      {trace.status === "clear" && (
        <Card className="p-5">
          <div className="text-[15px] font-semibold">Your foundations hold.</div>
          <p className="mt-1 text-[13.5px] text-muted">Every idea underneath is solid, so the gap is in {trace.title} itself. Read its notes and do a short practice set on it.</p>
        </Card>
      )}

      {root && (trace.status === "found" || trace.status === "fixed") && (
        <Card className="p-5">
          <div className="flex flex-wrap items-center gap-2">
            <Sparkles className="h-4 w-4 text-red" />
            <span className="text-[15px] font-semibold">The real gap: {root.idea}</span>
            <Badge>{where(root)}</Badge>
          </div>
          <p className="mt-1 text-[13.5px] text-muted">Fix this first and {trace.title} gets much easier. Your coach will plan it first too.</p>
          {!trace.lesson ? (
            <Button variant="primary" className="mt-4" onClick={() => lesson.mutate()} loading={lesson.isPending}>Fix it in 5 minutes</Button>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="rounded-xl bg-bg-soft p-4 text-[14px] leading-relaxed"><Markdown>{trace.lesson.md}</Markdown></div>
              <div>
                <div className="flex gap-2 text-[14px] font-medium"><CircleHelp className="mt-0.5 h-4 w-4 shrink-0" /><Markdown>{trace.lesson.check.q}</Markdown></div>
                <Options check={trace.lesson.check} value={trace.lesson.result ? trace.lesson.choice : pick}
                  locked={trace.lesson.result === "right"} onPick={setPick} />
                {trace.status === "fixed" ? (
                  <p className="mt-3 flex items-center gap-2 text-[14px] font-medium text-ok"><Check className="h-4 w-4" /> Gap closed. Go back to {trace.title}: it should click now.</p>
                ) : (
                  <div className="mt-3 flex items-center gap-3">
                    <Button variant="primary" size="sm" disabled={pick === null} onClick={() => pick !== null && recheck.mutate(pick)} loading={recheck.isPending}>Check</Button>
                    {trace.lesson.result === "wrong" && <span className="text-[13px] text-bad">Not yet. Read the example once more and try again.</span>}
                  </div>
                )}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function Picker({ onStart, busy }: { onStart: (chapterId: string, topicId?: string | null) => void; busy: boolean }) {
  const { data } = useQuery({ queryKey: ["gaps"], queryFn: api.gaps });
  const [q, setQ] = useState("");
  const matches = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!data || term.length < 2) return [];
    return data.chapters.filter((c) => `${c.name} ${c.subject}`.toLowerCase().includes(term)).slice(0, 8);
  }, [data, q]);
  if (!data) return <Skeleton className="h-48" />;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader title="What doesn't make sense?" icon={<Search className="h-4 w-4" />}
          subtitle="Pick a chapter. Edify traces it back through the earlier classes to the idea you're missing." />
        <div className="space-y-3 px-5 pb-5 pt-4">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Rotational motion, Electrostatics, Trigonometry" aria-label="Search chapters" />
          {matches.length > 0 && (
            <div className="divide-y divide-line rounded-xl border border-line">
              {matches.map((c) => (
                <button key={c.id} type="button" disabled={busy} onClick={() => onStart(c.id)}
                  className="flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left text-[14px] hover:bg-hover">
                  <span>{c.name}</span><span className="text-[12px] text-muted">{c.subject}{c.cls >= 1 && c.cls <= 12 ? ` · Class ${c.cls}` : ""}</span>
                </button>
              ))}
            </div>
          )}
          {data.suggestions.length > 0 && (
            <div>
              <div className="caps mb-2 text-[11px] font-medium text-muted">From your weak spots</div>
              <div className="flex flex-wrap gap-2">
                {data.suggestions.map((s) => (
                  <Button key={`${s.chapter_id}${s.topic_id}`} size="sm" variant="secondary" disabled={busy} onClick={() => onStart(s.chapter_id, s.topic_id)}>
                    {s.name} <span className="text-muted">· lost {s.misses}</span>
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

export default function RootCause() {
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const id = Number(params.get("trace")) || null;
  const { data: overview } = useQuery({ queryKey: ["gaps"], queryFn: api.gaps });
  const { data: trace } = useQuery({ queryKey: ["gap", id], queryFn: () => api.gap(id!), enabled: !!id });
  const start = useMutation({
    mutationFn: ({ chapterId, topicId }: { chapterId: string; topicId?: string | null }) => api.gapStart(chapterId, topicId),
    onSuccess: (t) => { qc.setQueryData(["gap", t.id], t); qc.invalidateQueries({ queryKey: ["gaps"] }); setParams({ trace: String(t.id) }); },
    onError: failed("Couldn't trace that chapter right now"),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader eyebrow="Root cause" title="Find the real gap"
        subtitle="Most topics don't make sense because of something from an earlier class. Find it, fix it in five minutes, then go back."
        actions={id ? <Button variant="secondary" size="sm" onClick={() => setParams({})}>Trace another topic</Button> : undefined} />

      {start.isPending && (
        <Card className="flex items-center gap-3 p-5 text-[14px]">
          <GitBranch className="h-5 w-5 animate-pulse" /> Tracing it back through the earlier classes…
        </Card>
      )}
      {id ? (trace ? <Chain key={trace.id} trace={trace} /> : <Skeleton className="h-72" />)
        : !start.isPending && <Picker busy={start.isPending} onStart={(chapterId, topicId) => start.mutate({ chapterId, topicId })} />}

      {!id && overview && (overview.traces.length ? (
        <Card>
          <CardHeader title="Your traces" icon={<GitBranch className="h-4 w-4" />}
            subtitle={overview.fixed ? `${overview.fixed} root gap${overview.fixed === 1 ? "" : "s"} fixed` : "Each one checked against the classes before it"} />
          <div className="divide-y divide-line px-2 pb-2 pt-3">
            {overview.traces.map((t) => (
              <button key={t.id} type="button" onClick={() => setParams({ trace: String(t.id) })}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-3 text-left hover:bg-hover">
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[14px] font-medium">{t.title}</span>
                  <span className="block truncate text-[12.5px] text-muted">
                    {t.root !== null ? `Root: ${t.chain[t.root].idea} (${where(t.chain[t.root])})` : t.chain.map((l) => l.idea).join(" ← ")}
                  </span>
                </span>
                <Badge tone={STATUS[t.status].tone}>{STATUS[t.status].label}</Badge>
                <span className="hidden text-[12px] text-muted sm:block">{t.created_at ? timeAgo(t.created_at) : ""}</span>
              </button>
            ))}
          </div>
        </Card>
      ) : (
        <EmptyState icon={<GitBranch className="h-5 w-5" />} title="No traces yet"
          body="Rotational motion, electrostatics, trigonometry: pick whatever isn't clicking." />
      ))}
    </div>
  );
}
