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

export function Sparkline({
  data,
  positive = true,
}: {
  data: PricePoint[];
  positive?: boolean;
}) {
  return (
    <svg
      viewBox="0 0 100 30"
      className="sparkline"
      aria-label="Recent closing price trend"
      role="img"
    >
      <path
        d={(() => {
          const points = data.slice(-22).map((p) => p.close);
          if (points.length < 2) return "";
          const lo = Math.min(...points),
            hi = Math.max(...points);
          return points
            .map(
              (p, i) =>
                `${i === 0 ? "M" : "L"}${((i / (points.length - 1)) * 98 + 1).toFixed(1)},${(27 - ((p - lo) / (hi - lo || 1)) * 24).toFixed(1)}`,
            )
            .join(" ");
        })()}
        fill="none"
        stroke={positive ? "#3c806c" : "#bd7567"}
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}
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
              <stop offset="0%" stopColor="#2d7761" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#2d7761" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke="#e8ebe5"
            strokeDasharray="3 5"
          />
          <XAxis
            dataKey="date"
            tickLine={false}
            axisLine={false}
            minTickGap={32}
            tick={{ fontSize: 10, fill: "#8a918a" }}
            tickFormatter={(v) => String(v).slice(5)}
          />
          <YAxis
            domain={["dataMin", "dataMax"]}
            tickLine={false}
            axisLine={false}
            width={52}
            tick={{ fontSize: 10, fill: "#8a918a" }}
            tickFormatter={(v) =>
              Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })
            }
          />
          <Tooltip
            contentStyle={{
              borderRadius: 10,
              border: "1px solid #e4e8e0",
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
            stroke="#2d7761"
            fill="url(#pricefill)"
            strokeWidth={2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
