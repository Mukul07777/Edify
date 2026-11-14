import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, GitBranch, Hand, Lightbulb, MapPinned, NotebookPen, Sparkles, Target, Waves, XCircle } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { PageHeader } from "@/components/common";
import { Markdown } from "@/components/Markdown";
import { Button } from "@/components/ui/button";
import { Badge, Card, CardHeader, EmptyState } from "@/components/ui/primitives";
import type { NextClassKit } from "@/lib/types";
import { api, ApiError } from "@/lib/api";
import { displayStyle } from "@/lib/math";
import { LETTERS } from "@/lib/utils";

/** What to do next class about one board: read from the wrong options picked, the doubts and the "I'm lost" taps. */
function KitPanel({ kit }: { kit: NextClassKit }) {
  return (
    <div className="mt-3 grid gap-4 rounded-2xl border border-line bg-bg-soft p-4 text-[13.5px] md:grid-cols-2">
      <div className="space-y-3">
        <div>
          <div className="caps mb-1 text-[11px] font-medium text-muted">What's in their heads</div>
          <Markdown className="font-medium">{kit.misconception}</Markdown>
        </div>
        <div>
          <div className="caps mb-1 text-[11px] font-medium text-muted">Say it simpler</div>
          <Markdown>{kit.simpler}</Markdown>
        </div>
        {kit.analogy && <div className="flex gap-2"><Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-warn" /><Markdown>{kit.analogy}</Markdown></div>}
        {kit.root_idea && (
          <p className="flex gap-2 text-muted"><GitBranch className="mt-0.5 h-4 w-4 shrink-0" />
            <span>Probably missing underneath: <b className="text-fg">{kit.root_idea}</b>{kit.root_class ? ` (Class ${kit.root_class})` : ""}. A two-minute recap of it first will help.</span></p>
        )}
      </div>
      <div className="space-y-3">
        {kit.board_plan.length > 0 && (
          <div>
            <div className="caps mb-1 flex items-center gap-1.5 text-[11px] font-medium text-muted"><NotebookPen className="h-3.5 w-3.5" /> On the board</div>
            <ol className="list-decimal space-y-1 rounded-xl bg-board p-3 pl-8 font-mono text-[12.5px] text-white/90 [&_*]:!text-white/90">
              {kit.board_plan.map((line) => <li key={line}><Markdown className="inline [&_p]:inline">{line}</Markdown></li>)}
            </ol>
          </div>
        )}
        {kit.openers.map((q, i) => (
          <div key={q.q}>
            <div className="caps mb-1 text-[11px] font-medium text-muted">Open the class with {i ? "another" : "this"}</div>
            <Markdown>{q.q}</Markdown>
            <ul className="mt-1 grid grid-cols-2 gap-1 text-[12.5px]">
              {q.options.map((o, j) => <li key={j} className={j === q.answer ? "font-semibold text-ok" : "text-muted"}>{LETTERS[j]}. <Markdown className="inline [&_p]:inline">{o}</Markdown></li>)}
            </ul>
          </div>
        ))}
        <p className="text-[12px] text-muted">From {kit.evidence.lost} "I'm lost" taps, {kit.evidence.wrong} wrong answers and {kit.evidence.doubts} doubts on this board.</p>
      </div>
    </div>
  );
}

/** The host's confusion map: the boards of a room's lecture ranked by how many students they lost, from
    anonymous "I'm lost" taps, wrong pop-quiz answers and doubts. Counts only, never names. */
export default function RoomReport() {
  const code = (useParams().code ?? "").toUpperCase();
  const { data, error, isLoading } = useQuery({
    queryKey: ["room-report", code], queryFn: () => api.roomReport(code), retry: false,
    refetchInterval: (q) => (q.state.data?.is_active ? 10_000 : false),
  });
  const fail = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "That didn't work. Try again.");
  const recap = useMutation({ mutationFn: (noteId: number) => api.roomRecap(code, noteId), onSuccess: () => toast.success("Recap sent to the room"), onError: fail });
  const check = useMutation({ mutationFn: (noteId: number) => api.roomQuiz(code, 30, noteId), onSuccess: () => toast.success("Question sent to the room"), onError: fail });
  const [kits, setKits] = useState<Record<number, NextClassKit>>({});
  const kit = useMutation({ mutationFn: (noteId: number) => api.nextClassKit(code, noteId), onSuccess: (k, noteId) => setKits((m) => ({ ...m, [noteId]: k })), onError: fail });

  const back = (
    <Link to={data?.is_active ? `/app/rooms/${code}` : "/app/rooms"} className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg">
      <ArrowLeft className="h-4 w-4" />{data?.is_active ? "Back to the room" : "Rooms"}
    </Link>
  );
  if (error) return <div className="space-y-4">{back}<EmptyState icon={<MapPinned className="h-5 w-5" />} title="No confusion map here" body={(error as Error).message} /></div>;
  if (isLoading || !data) return <div className="py-20 text-center text-sm text-muted">Reading the room…</div>;

  const t = data.totals;
  const quiet = !t.lost && !t.wrong && !t.doubts;
  return (
    <div className="space-y-4">
      {back}
      <PageHeader eyebrow="The return lane" title="Confusion map"
        subtitle={`${data.name}${data.topic ? ` · ${data.topic}` : ""}. Where the lecture lost students, board by board: "I'm lost" taps, wrong answers and doubts. Counts only, never names.`}
        actions={data.is_active ? <Badge tone="ok" dot="currentColor">Live: updates every 10 s</Badge> : <Badge>Room closed</Badge>} />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        {[
          [Waves, "I'm lost taps", t.lost],
          [XCircle, "Wrong answers", t.wrong],
          [Hand, "Doubts", t.doubts],
          [MapPinned, "Boards written", t.boards],
        ].map(([Icon, label, n]) => {
          const I = Icon as typeof Waves;
          return (
            <Card key={label as string} className="p-4">
              <div className="flex items-center gap-2 text-xs text-muted"><I className="h-3.5 w-3.5" />{label as string}</div>
              <div className="mt-1 font-display text-3xl tabular-nums">{n as number}</div>
            </Card>
          );
        })}
      </div>

      {quiet ? (
        <EmptyState icon={<MapPinned className="h-5 w-5" />} title="Nothing has lost the room yet"
          body={'Students tap "I\'m lost" under the lecture, and every wrong pop-quiz answer and doubt counts too. Each is pinned to the board on screen, so take notes for the room to see boards here.'} />
      ) : (
        <>
          <Card>
            <CardHeader title="The boards that lost the room" subtitle="Ranked by taps + wrong answers + doubts. Confidently wrong answers are the most dangerous misconceptions: they're marked." />
            <div className="divide-y divide-line">
              {data.boards.length === 0 && <p className="px-5 pb-5 text-sm text-muted">No board was on screen when these came in. Start "Take notes for the room" so each signal is pinned to a board.</p>}
              {data.boards.map((b, i) => (
                <div key={b.note_id} className="px-5 py-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-center">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-elev-2 text-sm font-semibold">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold">Board {b.number}: {b.topic}</div>
                    {b.excerpt && <div className="truncate text-sm text-muted">{b.excerpt}</div>}
                    <div className="mt-1.5 flex flex-wrap gap-1.5 text-xs">
                      <Badge tone={b.lost ? "warn" : "neutral"}><Waves className="h-3 w-3" />{b.lost} lost</Badge>
                      <Badge tone={b.wrong ? "bad" : "neutral"}><XCircle className="h-3 w-3" />{b.wrong} wrong</Badge>
                      <Badge><Hand className="h-3 w-3" />{b.doubts} {b.doubts === 1 ? "doubt" : "doubts"}</Badge>
                      {!!b.sure_wrong && <Badge tone="bad">{b.sure_wrong} confidently wrong</Badge>}
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-2">
                    {!kits[b.note_id] && (
                      <Button size="sm" variant={data.is_active ? "secondary" : "primary"} loading={kit.isPending && kit.variables === b.note_id}
                        onClick={() => kit.mutate(b.note_id)} icon={<NotebookPen className="h-3.5 w-3.5" />}>Next-class kit</Button>
                    )}
                  {data.is_active && (
                    <div className="flex shrink-0 gap-2">
                      <Button size="sm" variant="primary" loading={recap.isPending && recap.variables === b.note_id} onClick={() => recap.mutate(b.note_id)}
                        icon={<Sparkles className="h-3.5 w-3.5" />}>Re-explain</Button>
                      <Button size="sm" loading={check.isPending && check.variables === b.note_id} onClick={() => check.mutate(b.note_id)}
                        icon={<Target className="h-3.5 w-3.5" />}>Send a check</Button>
                    </div>
                  )}
                  </div>
                </div>
                {kits[b.note_id] && <KitPanel kit={kits[b.note_id]} />}
                </div>
              ))}
            </div>
          </Card>

          {data.timeline.length > 1 && (
            <Card>
              <CardHeader title="When the room got lost" subtitle="Signals per minute since the first one" />
              <div className="h-56 px-2 pb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.timeline} margin={{ top: 4, right: 12, bottom: 4, left: -16 }}>
                    <CartesianGrid vertical={false} stroke="var(--line)" />
                    <XAxis dataKey="minute" tickFormatter={(m) => `${m} min`} tick={{ fill: "var(--muted)", fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fill: "var(--muted)", fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 12 }} labelFormatter={(m) => `Minute ${m}`} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="lost" name="I'm lost" stackId="s" fill="var(--warn)" />
                    <Bar dataKey="wrong" name="Wrong answers" stackId="s" fill="var(--bad)" />
                    <Bar dataKey="doubts" name="Doubts" stackId="s" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader title="Pop quizzes" subtitle={`${t.quizzes} asked`} />
              <div className="space-y-4 px-5 pb-5">
                {data.quizzes.length === 0 && <p className="text-sm text-muted">No pop quiz yet.</p>}
                {data.quizzes.map((q, qi) => {
                  const total = q.answered || 1;
                  return (
                    <div key={qi}>
                      <div className="mb-1 flex items-start gap-2">
                        <Markdown className="flex-1 text-sm font-medium">{q.question}</Markdown>
                        <Badge tone={q.correct / total >= 0.7 ? "ok" : "warn"}>{q.correct}/{q.answered} right</Badge>
                      </div>
                      {q.board && <div className="mb-1.5 text-xs text-muted">On board {q.board}</div>}
                      <div className="space-y-1">
                        {q.options.map((o, i) => (
                          <div key={i} className="relative overflow-hidden rounded-lg border border-line px-2.5 py-1.5 text-xs">
                            <span className="absolute inset-y-0 left-0 bg-fg/5" style={{ width: `${(100 * (q.counts[i] ?? 0)) / total}%` }} />
                            <span className="relative flex items-center gap-2">
                              <b className={i === q.answer_index ? "text-ok" : ""}>{LETTERS[i]}</b>
                              <Markdown className="flex-1 text-xs">{displayStyle(o)}</Markdown>
                              <span className="tabular-nums text-muted">{q.counts[i] ?? 0}</span>
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
            <Card>
              <CardHeader title="Top doubts" subtitle="Most 'me too' votes first" />
              <div className="space-y-2 px-5 pb-5">
                {data.doubts.length === 0 && <p className="text-sm text-muted">No doubts raised.</p>}
                {data.doubts.map((d, i) => (
                  <div key={i} className="rounded-xl border border-line bg-bg-soft px-3 py-2 text-sm">
                    <div>{d.text}</div>
                    <div className="mt-1 flex gap-3 text-xs text-muted">
                      <span><Hand className="mr-1 inline h-3 w-3" />{d.votes} me too</span>
                      {d.board && <span>board {d.board}</span>}
                      {d.resolved && <span className="text-ok">resolved</span>}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
