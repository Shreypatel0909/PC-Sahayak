import { useCallback, useState } from 'react';
import type { Meta, Specs } from '../types';
import { checkImage, usePasteImage } from '../lib/images';
import { Attachment } from './Attachment';

interface Props {
  meta: Meta;
  active: boolean;
  busy: boolean;
  onStart: (specs: Specs, issue: string, image: File | null) => void;
  onError: (message: string) => void;
}

const pick = (value: string | null | undefined, options: string[], fallback: string) =>
  value && options.includes(value) ? value : fallback;

export function Intake({ meta, active, busy, onStart, onError }: Props) {
  const o = meta.options;
  const last = meta.last_specs;
  const [specs, setSpecs] = useState<Specs>(() => ({
    device_type: pick(last?.device_type, o.device_types, 'Laptop'),
    os: pick(last?.os, o.os, 'Windows 11'),
    os_version: last?.os_version ?? '',
    ram_size: pick(last?.ram_size, o.ram_sizes, '8 GB'),
    ram_type: pick(last?.ram_type, o.ram_types, "Don't know"),
    storage_size: pick(last?.storage_size, o.storage_sizes, '512 GB'),
    storage_type: pick(last?.storage_type, o.storage_types, "Don't know"),
  }));
  const [issue, setIssue] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [missing, setMissing] = useState(false);
  const [over, setOver] = useState(false);

  const set = (key: keyof Specs) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setSpecs(s => ({ ...s, [key]: e.target.value }));

  const take = useCallback((file: File) => {
    const problem = checkImage(file);
    if (problem) onError(problem); else { setImage(file); setMissing(false); }
  }, [onError]);
  usePasteImage(active && !busy, take);

  function choose() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/png,image/jpeg,image/webp';
    input.onchange = () => { const f = input.files?.[0]; if (f) take(f); };
    input.click();
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const text = issue.trim();
    if (!text && !image) { setMissing(true); document.getElementById('issue')?.focus(); return; }
    onStart({ ...specs, os_version: specs.os_version?.trim() || null }, text, image);
  }

  const select = (id: keyof Specs, label: string, options: string[]) => (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} value={specs[id] ?? ''} onChange={set(id)}>
        {options.map(v => <option key={v}>{v}</option>)}
      </select>
    </div>
  );

  return (
    <form className="intake" onSubmit={submit} noValidate hidden={!active}>
      <div>
        <h2>What's wrong with your PC?</h2>
        <p className="lede">Tell me about the computer once. I'll keep these details for the whole fix and won't ask for them again.</p>
      </div>

      <div className="examples">
        <span className="eyebrow">Or start from an example</span>
        <div className="chips">
          {meta.starter_suggestions.map(s => (
            <button className="chip" type="button" key={s} onClick={() => { setIssue(s); setMissing(false); document.getElementById('issue')?.focus(); }}>{s}</button>
          ))}
        </div>
      </div>

      <fieldset>
        <legend>Device</legend>
        <div className="seg">
          {o.device_types.map(d => (
            <label key={d}>
              <input type="radio" name="device" value={d} checked={specs.device_type === d} onChange={set('device_type')} />
              <span>{d}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid2">
        {select('os', 'Operating system', o.os)}
        <div className="field">
          <label htmlFor="os_version">Version or build</label>
          <input id="os_version" value={specs.os_version ?? ''} onChange={set('os_version')} placeholder="e.g. 23H2" />
        </div>
        {select('ram_size', 'RAM size', o.ram_sizes)}
        {select('ram_type', 'RAM type', o.ram_types)}
        {select('storage_size', 'Storage size', o.storage_sizes)}
        {select('storage_type', 'Storage type', o.storage_types)}
      </div>
      {last && <div className="prefill">Filled in from your last problem. Change anything that's different.</div>}

      <details className="howto">
        <summary>Not sure where to find these?</summary>
        <ul>
          <li><b>OS and version:</b> Settings › System › About, under Windows specifications.</li>
          <li><b>RAM size:</b> Settings › System › About, Installed RAM.</li>
          <li><b>RAM type:</b> Task Manager (<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Esc</kbd>) › Performance › Memory. About 2133–3200 MT/s is usually DDR4; 4800 MT/s and up is DDR5.</li>
          <li><b>Storage:</b> Task Manager › Performance › Disk 0 shows the size and whether it's an SSD or HDD.</li>
          <li>Not sure? Pick <b>Don't know</b>.</li>
        </ul>
      </details>

      <div className="field">
        <label htmlFor="issue">Describe the problem</label>
        <textarea id="issue" value={issue} maxLength={5000}
          onChange={e => { setIssue(e.target.value); setMissing(false); }}
          placeholder="What happens, when it started, and any error message you see" />
      </div>

      <div
        className={`drop${over ? ' over' : ''}`}
        onDragOver={e => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={e => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files[0]; if (f) take(f); }}
      >
        {image
          ? <Attachment file={image} onRemove={() => setImage(null)} />
          : <div><b>Add a screenshot</b> of the error (optional). Drop it here, paste with <kbd>Ctrl</kbd> + <kbd>V</kbd>, or <button className="link" type="button" onClick={choose}>choose a file</button>.</div>}
      </div>

      {missing && <p className="form-error" role="alert">Describe the problem or add a screenshot so I know where to start.</p>}
      <button className="start" type="submit" disabled={busy}>{busy ? <><span className="spin" />Starting…</> : 'Start troubleshooting'}</button>
    </form>
  );
}
