import { ImageOff } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useBackClose } from "@/lib/overlay";
import { cn } from "@/lib/utils";

/* ---------------------------------------------------------------- Logo */
/** The mark: a light bulb whose filament is the letter e. public/logo-mark.png holds its shape and is used as a
    mask, so it takes the text colour (ink on Paper, ivory on Ink). The icons in public/ are made from the same file. */
const MARK_MASK = "url(/logo-mark.png) center / contain no-repeat";

export function LogoMark({ className }: { className?: string }) {
  return (
    <span aria-hidden className={cn("inline-block h-8 w-8 shrink-0 bg-fg", className)}
      style={{ WebkitMask: MARK_MASK, mask: MARK_MASK }} />
  );
}

/** The mark and the name, set heavy and tight like the headlines. */
export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark className="h-6 w-6" />
      <span className="font-brand text-[21px] font-bold leading-none tracking-[-0.04em]">Edify</span>
    </span>
  );
}

/* ---------------------------------------------------------------- Auth-protected board snapshot */
const imageCache = new Map<string, string>();

/** `version` (e.g. the note's updated_at) busts the cache when a growing board replaces its snapshot. */
export function BoardImage({ noteId, version, className, onClick }: {
  noteId: number; version?: string | null; className?: string; onClick?: (src: string) => void;
}) {
  const key = `${noteId}:${version ?? ""}`;
  const [src, setSrc] = useState<string | null>(imageCache.get(key) ?? null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const cached = imageCache.get(key);
    if (cached) return setSrc(cached);
    let cancelled = false;
    api.noteImage(noteId)
      .then((r) => r.blob())
      .then((b) => {
        const url = URL.createObjectURL(b);
        imageCache.set(key, url);
        if (!cancelled) setSrc(url);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [noteId, key]);

  if (failed)
    return (
      <div className={cn("grid place-items-center bg-elev-2 text-muted", className)}>
        <ImageOff className="h-5 w-5" />
      </div>
    );
  if (!src) return <div className={cn("skeleton", className)} />;
  return (
    <img src={src} alt="Board snapshot" onClick={() => onClick?.(src)} loading="lazy"
      className={cn("object-cover", onClick && "cursor-zoom-in", className)} />
  );
}

/* ---------------------------------------------------------------- Activity heatmap */
export function PageHeader({ title, subtitle, actions, eyebrow }: {
  title: React.ReactNode; subtitle?: React.ReactNode; actions?: React.ReactNode; eyebrow?: React.ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <div className="eyebrow mb-3">{eyebrow}</div>}
        <h1 className="display-caps text-[34px] sm:text-[46px]">{title}</h1>
        {subtitle && <p className="mt-2.5 max-w-2xl text-[15px] leading-relaxed text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

/* ---------------------------------------------------------------- Image lightbox */
export function Lightbox({ src, onClose }: { src: string | null; onClose: () => void }) {
  useBackClose(!!src, onClose);
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  if (!src) return null;
  return (
    <div className="fixed inset-0 z-[60] grid cursor-zoom-out place-items-center bg-black/85 p-6 backdrop-blur" onClick={onClose}>
      <img src={src} alt="Board" className="max-h-full max-w-full" />
    </div>
  );
}
