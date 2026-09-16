import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import type { NumericalEvidence } from '@/types/evidence'
import { Panel, PanelHeader } from '@/components/Panel'

interface ChangeMetricsChartProps {
  evidence: NumericalEvidence
}

export function ChangeMetricsChart({ evidence }: ChangeMetricsChartProps) {
  const data = evidence.series || []

  return (
    <Panel>
      <PanelHeader
        title={evidence.label}
        subtitle="Quantitative multi-temporal surface trend analysis"
        action={
          <div className="flex items-center gap-1 font-mono-tabular text-sm font-semibold text-[var(--color-accent)]">
            <span>+{evidence.value}</span>
            <span className="text-xs font-normal text-[var(--color-text-muted)]">
              {evidence.unit}
            </span>
          </div>
        }
      />

      <div className="p-4">
        {data.length > 0 ? (
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis
                  dataKey="name"
                  tickLine={false}
                  axisLine={{ stroke: '#2b4b56' }}
                  tick={{ fill: '#7e97a0', fontSize: 11 }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={{ stroke: '#2b4b56' }}
                  tick={{ fill: '#7e97a0', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#16303a',
                    border: '1px solid #3d6373',
                    borderRadius: '8px',
                    color: '#f2ede4',
                    fontSize: '12px',
                  }}
                  itemStyle={{ color: '#e08a5b' }}
                />
                <Bar dataKey="value" fill="#e08a5b" radius={[4, 4, 0, 0]} name="Surface Footprint" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-xs text-[var(--color-text-muted)]">
            No temporal series metrics provided for this analysis.
          </p>
        )}
      </div>
    </Panel>
  )
}
