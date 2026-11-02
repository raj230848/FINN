import type {PricePoint} from "@/lib/api";
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
        stroke={positive ? "var(--positive)" : "var(--negative)"}
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}
