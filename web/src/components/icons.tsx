const base = { fill: 'none', stroke: 'currentColor', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

export const Logo = () => (
  <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
    <rect x="3" y="13" width="24" height="4" rx="2" fill="var(--line)" />
    <rect x="1" y="9" width="10" height="12" rx="4" fill="var(--line)" />
    <circle cx="17" cy="15" r="4.5" fill="var(--surface)" stroke="var(--line)" strokeWidth="3" />
    <circle cx="26" cy="15" r="3" fill="var(--surface)" stroke="var(--muted)" strokeWidth="2" strokeDasharray="2 2" />
  </svg>
);

export const BotMark = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base} strokeWidth="2.5" aria-hidden="true">
    <path d="M3 12h18" /><circle cx="8" cy="12" r="3" fill="currentColor" /><circle cx="17" cy="12" r="3" />
  </svg>
);

export const Sun = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base} strokeWidth="2" aria-hidden="true">
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </svg>
);

export const Moon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base} strokeWidth="2" aria-hidden="true">
    <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
  </svg>
);

export const Gear = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base} strokeWidth="2" aria-hidden="true">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
  </svg>
);

export const Plus = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...base} strokeWidth="3" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>
);

export const Menu = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base} strokeWidth="2.2" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10" /></svg>
);

export const Close = ({ size = 16 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} strokeWidth="2.5" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
);

export const Trash = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...base} strokeWidth="2" aria-hidden="true">
    <path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" />
  </svg>
);

export const Clip = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" {...base} strokeWidth="2" aria-hidden="true">
    <path d="M21.4 11.1l-8.5 8.5a5.5 5.5 0 0 1-7.8-7.8l8.5-8.5a3.7 3.7 0 0 1 5.2 5.2l-8.5 8.5a1.8 1.8 0 0 1-2.6-2.6l7.8-7.8" />
  </svg>
);

export const Arrow = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base} strokeWidth="2.5" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
);
