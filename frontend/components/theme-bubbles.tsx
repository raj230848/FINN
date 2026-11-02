/** Decorative, static spheres behind the workspace; never intercept input. */
export function ThemeBubbles() {
  return <div className="theme-bubbles" aria-hidden="true">
    {Array.from({length:15},(_,index)=><span className="theme-bubble" key={index}/>)}
  </div>;
}
