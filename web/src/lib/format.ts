export function when(seconds: number): string {
  const ts = seconds * 1000;
  const d = Date.now() - ts;
  const t = new Date(ts);
  if (d < 60e3) return 'just now';
  if (d < 3600e3) return `${Math.round(d / 60e3)} min ago`;
  if (new Date().toDateString() === t.toDateString()) return `today ${t.toTimeString().slice(0, 5)}`;
  if (d < 2 * 86400e3) return 'yesterday';
  return t.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

export function clip(s: string, n: number): string {
  const t = s.trim();
  return t.length > n ? t.slice(0, n - 1).trimEnd() + '…' : t;
}

export const prettyFile = (file: string) => file.replace(/\\/g, '/').split('/').pop() || file;
