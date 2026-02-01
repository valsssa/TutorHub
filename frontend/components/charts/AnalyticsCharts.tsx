"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const COLORS = ["#10b981", "#3b82f6", "#8b5cf6", "#f59e0b", "#ef4444"];

interface RevenueChartProps {
  data: Array<{ month: string; revenue: number; sessions: number }>;
}

export function RevenueChart({ data }: RevenueChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="month" stroke="#64748b" />
        <YAxis stroke="#64748b" />
        <Tooltip
          contentStyle={{
            backgroundColor: "#fff",
            borderRadius: "0.5rem",
            borderColor: "#e2e8f0",
          }}
        />
        <Legend />
        <Bar dataKey="revenue" fill="#10b981" name="Revenue ($)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="sessions" fill="#3b82f6" name="Sessions" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface UserGrowthChartProps {
  data: Array<{ month: string; users: number; tutors: number; students: number }>;
}

export function UserGrowthChart({ data }: UserGrowthChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="month" stroke="#64748b" />
        <YAxis stroke="#64748b" />
        <Tooltip
          contentStyle={{
            backgroundColor: "#fff",
            borderRadius: "0.5rem",
            borderColor: "#e2e8f0",
          }}
        />
        <Legend />
        <Line type="monotone" dataKey="users" stroke="#10b981" name="Total Users" strokeWidth={2} />
        <Line type="monotone" dataKey="tutors" stroke="#3b82f6" name="Tutors" strokeWidth={2} />
        <Line type="monotone" dataKey="students" stroke="#8b5cf6" name="Students" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}

interface SubjectDistributionChartProps {
  data: Array<{ name: string; value: number }>;
}

export function SubjectDistributionChart({ data }: SubjectDistributionChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

// Default export for lazy loading the entire module
export default function AnalyticsCharts() {
  return null; // Placeholder - individual components should be imported
}
