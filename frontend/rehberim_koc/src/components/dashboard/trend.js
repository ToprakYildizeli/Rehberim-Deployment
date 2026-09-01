import { TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';

/** Shared mapping so trend chips look identical in the table, cards and modal. */
export function trendMeta(trend) {
  if (trend === 'up') return { tone: 'success', label: 'Yükseliş', Icon: TrendingUp };
  if (trend === 'down') return { tone: 'danger', label: 'Düşüş', Icon: TrendingDown };
  return { tone: 'warning', label: 'Sabit', Icon: ArrowRight };
}
