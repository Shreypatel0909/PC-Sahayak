import { useEffect, useState } from 'react';
import { Close } from './icons';

/** Thumbnail + file name + remove button for a screenshot waiting to be sent. */
export function Attachment({ file, onRemove }: { file: File; onRemove: () => void }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);
  return (
    <div className="attached">
      {url && <img src={url} alt="" />}
      <span>{file.name || 'Pasted screenshot'}</span>
      <button className="x" type="button" onClick={onRemove} aria-label="Remove screenshot"><Close size={14} /></button>
    </div>
  );
}
