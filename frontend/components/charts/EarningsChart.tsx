"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface EarningsChartProps {
  data: Array<{ name: string; earnings: number }>;
}

export default function EarningsChart({ data }: EarningsChartProps) {
  if (data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        No earnings data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%" minWidth={0}>
      <BarChart data={data}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#94a3b8"
          strokeOpacity={0.1}
          vertical={false}
        />
        <XAxis
          dataKey="name"
          stroke="#64748b"
          axisLine={false}
          tickLine={false}
          dy={10}
          fontSize={12}
        />
        <YAxis
          stroke="#64748b"
          axisLine={false}
          tickLine={false}
          tickFormatter={(value) => `$${value}`}
          fontSize={12}
        />
        <Tooltip
          cursor={{ fill: "rgba(148, 163, 184, 0.1)" }}
          formatter={(value: number) => [`$${Number(value).toFixed(2)}`, "Earnings"]}
          labelFormatter={(label) => label}
          contentStyle={{
            backgroundColor: "hsl(var(--background))",
            borderColor: "hsl(var(--border))",
            borderRadius: "0.5rem",
            boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
            color: "hsl(var(--foreground))",
          }}
        />
        <Bar dataKey="earnings" fill="#10b981" radius={[4, 4, 0, 0]} barSize={40} />
      </BarChart>
    </ResponsiveContainer>
  );
}
