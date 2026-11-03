/** Decorative market artwork behind the workspace; never intercepts input. */
export function ThemeBubbles() {
  return <div className="market-backdrop" aria-hidden="true"><span className="market-art market-art-globe"/><span className="market-art market-art-stocks"/></div>;
}
