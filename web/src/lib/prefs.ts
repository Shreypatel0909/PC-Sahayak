import { useCallback, useEffect, useState } from 'react';

export type ThemePref = 'system' | 'light' | 'dark';

export interface Prefs {
  theme: ThemePref;
  animate: boolean;
}

const KEY = 'pc-helper-prefs';
const DEFAULTS: Prefs = { theme: 'system', animate: true };

function load(): Prefs {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || '{}') };
  } catch {
    return DEFAULTS;
  }
}

const darkQuery = () => window.matchMedia('(prefers-color-scheme: dark)');

/** Per-browser display preferences (theme, reply animation). */
export function usePrefs() {
  const [prefs, setPrefs] = useState<Prefs>(load);
  const [systemDark, setSystemDark] = useState(() => darkQuery().matches);

  useEffect(() => {
    const mq = darkQuery();
    const onChange = () => setSystemDark(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    if (prefs.theme === 'system') delete root.dataset.theme;
    else root.dataset.theme = prefs.theme;
    try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch { /* storage blocked */ }
  }, [prefs]);

  const update = useCallback((patch: Partial<Prefs>) => setPrefs(p => ({ ...p, ...patch })), []);
  const isDark = prefs.theme === 'dark' || (prefs.theme === 'system' && systemDark);
  return { prefs, update, isDark };
}
