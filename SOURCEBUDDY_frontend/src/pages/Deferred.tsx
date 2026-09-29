interface DeferredProps {
  title: string;
  note?: string;
}

export default function Deferred({ title, note }: DeferredProps) {
  return (
    <div className="min-h-screen grid place-items-center">
      <div className="max-w-md text-center">
        <p className="font-mono text-[11px] uppercase tracking-[.28em] text-white/40">
          Not available
        </p>
        <h2 className="mt-3 font-display italic text-3xl text-white">
          {title}
        </h2>
        <p className="mt-3 text-sm text-white/55 leading-relaxed">
          {note ?? 'This feature is not yet implemented.'}
        </p>
      </div>
    </div>
  );
}