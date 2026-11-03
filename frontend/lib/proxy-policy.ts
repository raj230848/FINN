/** Give bounded PDF imports time to download and index without slowing other APIs. */
export function backendTimeoutMs(method:string,path:readonly string[]):number {
  return method==="POST"&&path.length===1&&path[0]==="documents"?180000:55000;
}

const guestReads = new Set(["health", "companies", "company-search", "dashboard", "announcements", "alerts", "notifications", "preferences", "push/config"]);

export function guestAllows(method: string, path: readonly string[]): boolean {
  if (path.some(segment => !/^[\w.&-]+$/.test(segment) || segment === "." || segment === "..")) return false;
  const route = path.join("/");
  if (method === "POST") return route === "research";
  if (method !== "GET") return false;
  return guestReads.has(route)
    || /^companies\/[\w.&-]+\/(documents|financials|guidance)$/.test(route)
    || /^announcements\/\d+\/context$/.test(route)
    || /^sync\/\d+$/.test(route);
}
