// Split an assistant reply into the sections the system prompt asks for
// ("What I understand", "Next step", ...) so each can get its own treatment.
// Replies that don't follow the format render as one plain block.

export type SectionKind = 'intro' | 'understand' | 'finding' | 'step' | 'expect' | 'ask';

export interface Section {
  kind: SectionKind;
  label: string;
  md: string;
}

const LABELS: Array<[RegExp, SectionKind, string]> = [
  [/^what i understand$/i, 'understand', 'What I understand'],
  [/^current finding$/i, 'finding', 'Current finding'],
  [/^next step$/i, 'step', 'Next step'],
  [/^expected result$/i, 'expect', 'Expected result'],
  [/^tell me what happened$/i, 'ask', 'Tell me what happened'],
  // closing summary
  [/^fixed$/i, 'finding', 'Fixed'],
  [/^what we did$/i, 'finding', 'What we did'],
  [/^why it worked$/i, 'finding', 'Why it worked'],
  [/^keep it from coming back$/i, 'finding', 'Keep it from coming back'],
];

// "**Next step**", "### Next step:", "**Next step:** do X", "Next step — do X"
const HEADER = /^\s*(?:#{1,4}\s*)?(?:\*\*|__)?\s*(what i understand|current finding|next step|expected result|tell me what happened|fixed|what we did|why it worked|keep it from coming back)\s*:?\s*(?:\*\*|__)?\s*:?\s*(?:[—–-]\s*)?(.*)$/i;

export function parseReply(text: string): Section[] {
  const sections: Section[] = [];
  let cur: Section = { kind: 'intro', label: '', md: '' };
  for (const line of text.split(/\r?\n/)) {
    // Only bold/heading lines or "Label:" count, so a sentence like "Fixed the cable" stays text.
    const marked = /^\s*(#{1,4}\s|\*\*|__)/.test(line) || /^\s*[a-z ]+:/i.test(line);
    const m = marked ? HEADER.exec(line) : null;
    const match = m && LABELS.find(([re]) => re.test(m[1].trim()));
    if (m && match) {
      if (cur.md.trim()) sections.push(cur);
      cur = { kind: match[1], label: match[2], md: m[2] ? m[2] + '\n' : '' };
    } else {
      cur.md += line + '\n';
    }
  }
  if (cur.md.trim()) sections.push(cur);
  return sections.map(s => ({ ...s, md: s.md.trim() }));
}

export const hasStep = (text: string) => parseReply(text).some(s => s.kind === 'step');
