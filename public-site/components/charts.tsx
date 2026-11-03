"use client";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PricePoint } from "@/lib/api";

export {Sparkline} from "./sparkline";
export function PriceChart({ data }: { data: PricePoint[] }) {
  return (
    <div className="price-chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
        >
          <defs>
            <linearGradient id="pricefill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-line)" stopOpacity={0.2} />
              <stop offset="100%" stopColor="var(--chart-line)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke="var(--chart-grid)"
            strokeDasharray="3 5"
          />
          <XAxis
            dataKey="date"
            tickLine={false}
            axisLine={false}
            minTickGap={32}
            tick={{ fontSize: 10, fill: "var(--text-muted)" }}
            tickFormatter={(v) => String(v).slice(5)}
          />
          <YAxis
            domain={["dataMin", "dataMax"]}
            tickLine={false}
            axisLine={false}
            width={52}
            tick={{ fontSize: 10, fill: "var(--text-muted)" }}
            tickFormatter={(v) =>
              Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })
            }
          />
          <Tooltip
            contentStyle={{
              borderRadius: 10,
              backgroundColor: "var(--surface-raised)",
              color: "var(--text)",
              border: "1px solid var(--border-strong)",
              fontSize: 12,
            }}
            formatter={(value) => [
              Number(value).toLocaleString("en-IN", {
                maximumFractionDigits: 2,
              }),
              "Adjusted close ₹",
            ]}
          />
          <Area
            dataKey="close"
            type="monotone"
            stroke="var(--chart-line)"
            fill="url(#pricefill)"
            strokeWidth={2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
