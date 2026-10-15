import { useEffect } from 'react';

const TYPES = ['image/png', 'image/jpeg', 'image/webp'];
const MAX_BYTES = 10 * 1024 * 1024;

/** Return an error message for an unusable screenshot, or null if it's fine. */
export function checkImage(file: File): string | null {
  if (!TYPES.includes(file.type)) return 'Use a PNG, JPG or WebP image.';
  if (file.size > MAX_BYTES) return 'That screenshot is over 10 MB. Try a smaller image.';
  return null;
}

/** Call `onImage` when the user pastes an image anywhere on the page (while `active`). */
export function usePasteImage(active: boolean, onImage: (file: File) => void) {
  useEffect(() => {
    if (!active) return;
    const onPaste = (e: ClipboardEvent) => {
      const file = [...(e.clipboardData?.files ?? [])].find(f => f.type.startsWith('image/'));
      if (!file) return;
      e.preventDefault();
      onImage(file);
    };
    document.addEventListener('paste', onPaste);
    return () => document.removeEventListener('paste', onPaste);
  }, [active, onImage]);
}
