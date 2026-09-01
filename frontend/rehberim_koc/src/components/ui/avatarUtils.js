const AVATAR_COLORS = [
  '#3b5bdb', '#7c3aed', '#f59e0b', '#10b981',
  '#ef4444', '#06b6d4', '#ec4899', '#6366f1',
];

export function initialsOf(name = '') {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0] || '')
    .join('')
    .toLocaleUpperCase('tr-TR');
}

export function colorFor(name = '') {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}
