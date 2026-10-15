import { Fragment, useEffect, useRef } from 'react';
import { CATEGORY_NAMES, type Conversation, type Specs } from '../types';
import { clip, prettyFile } from '../lib/format';

type StopKind = 'origin' | 'done' | 'current' | 'fixed' | 'next';
interface Stop { kind: StopKind; title: string; note?: string }

function stopsOf(c: Conversation): Stop[] {
  const r = c.route;
  const stops: Stop[] = [{ kind: 'origin', title: r.origin, note: 'Reported' }];
  r.done.forEach(t => stops.push({ kind: 'done', title: t }));
  if (r.current) stops.push({ kind: 'current', title: r.current, note: 'Your step now' });
  if (r.fixed) stops.push({ kind: 'fixed', title: 'Fixed', note: 'Confirmed by you' });
  else stops.push({ kind: 'next', title: 'Depends on what you see' });
  return stops;
}

const MARK: Record<StopKind, string> = { origin: '', done: '✓', current: '', fixed: '✓', next: '?' };

/** Transit-style route: one stop per troubleshooting step (desktop side panel). */
export function RoutePanel({ conv }: { conv: Conversation | null }) {
  const mapped = conv && conv.route.origin ? conv : null;
  const stops = mapped ? stopsOf(mapped) : [];
  return (
    <aside className="pane side" aria-label="Fix route">
      <section className="panel">
        <div className="route-head">
          <span className="line-name">{mapped ? `${CATEGORY_NAMES[mapped.category]} line` : 'No line yet'}</span>
          {mapped && conv && <span className={`status${conv.route.fixed ? ' ok' : ''}`}>{conv.route.fixed ? 'fixed' : conv.status === 'needs_info' ? 'needs info' : 'diagnosing'}</span>}
        </div>
        {mapped ? (
          <ol className="stops">
            {stops.map((s, i) => (
              <li key={`${s.kind}-${i}-${s.title}`} className={`stop ${s.kind}${s.kind === 'origin' && stops[i + 1]?.kind === 'next' ? ' solo' : ''}`}>
                <span className="dot" aria-hidden="true">{MARK[s.kind]}</span>
                <b>{s.title}</b>
                {s.note && <small>{s.note}</small>}
              </li>
            ))}
          </ol>
        ) : (
          <div className="route-empty"><i /><div>Your route appears here once you describe the problem. Each step you try becomes a stop.</div></div>
        )}
      </section>

      <section className="panel">
        <span className="eyebrow">This PC</span>
        <SpecList specs={conv?.specs ?? null} />
      </section>

      <section className="panel">
        <span className="eyebrow">Checked against</span>
        {conv && conv.sources.length > 0 ? (
          <ul className="kb">
            {conv.sources.map(s => <li key={s.file + s.heading}>{prettyFile(s.file)}{s.heading && <span>{s.heading}</span>}</li>)}
          </ul>
        ) : <p className="muted-line">Guides used for this problem show up here.</p>}
      </section>
    </aside>
  );
}

const known = (v: string | null | undefined) => !!v && v !== "Don't know";

function SpecList({ specs }: { specs: Specs | null }) {
  if (!specs) return <p className="muted-line">Filled in from the form when you start.</p>;
  const join = (...v: Array<string | null>) => v.filter(known).join(' ');
  const rows = [
    ['Device', specs.device_type ?? ''],
    ['System', join(specs.os, specs.os_version)],
    ['Memory', join(specs.ram_size, specs.ram_type)],
    ['Storage', join(specs.storage_size, specs.storage_type)],
  ].filter(([, v]) => known(v));
  if (!rows.length) return <p className="muted-line">No details given for this PC.</p>;
  return <dl className="spec-list">{rows.map(([k, v]) => <Fragment key={k}><dt>{k}</dt><dd>{v}</dd></Fragment>)}</dl>;
}

/** The same route as a horizontal strip (phones). */
export function RouteStrip({ conv }: { conv: Conversation }) {
  const ref = useRef<HTMLDivElement>(null);
  const stops = stopsOf(conv);
  useEffect(() => {
    const cur = ref.current?.querySelector<HTMLElement>('.cur');
    if (cur && ref.current) ref.current.scrollLeft = cur.offsetLeft - 60;
  }, [conv]);
  return (
    <div className="strip" ref={ref} aria-label="Fix route">
      {stops.map((s, i) => {
        const cls = s.kind === 'current' ? ' cur' : s.kind === 'next' ? ' nx' : s.kind === 'fixed' ? ' fx' : '';
        const label = s.kind === 'origin' ? 'Reported' : s.kind === 'next' ? 'Next' : clip(s.title, 22);
        return (
          <Fragment key={i}>
            {i > 0 && <span className={`bar${s.kind === 'next' ? ' dash' : ''}`} />}
            <span className={`s${cls}`}><i />{label}</span>
          </Fragment>
        );
      })}
    </div>
  );
}
