const FALLBACK_API_URL = "https://api.valsa.solutions";
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);

const isLocalHost = (hostname: string): boolean => {
  if (LOCAL_HOSTS.has(hostname)) {
    return true;
  }
  return hostname.endsWith(".local");
};

const shouldUpgradeToHttps = (hostname: string, protocol: string): boolean => {
  return protocol === "http:" && hostname.endsWith("valsa.solutions") && !isLocalHost(hostname);
};

const shouldUpgradeToWss = (hostname: string, protocol: string): boolean => {
  return protocol === "ws:" && hostname.endsWith("valsa.solutions") && !isLocalHost(hostname);
};

export const getApiBaseUrl = (raw?: string): string => {
  const candidate = raw?.trim() || FALLBACK_API_URL;

  try {
    const url = new URL(candidate);
    if (shouldUpgradeToHttps(url.hostname, url.protocol)) {
      url.protocol = "https:";
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    return candidate;
  }
};

export const getWebSocketBaseUrl = (rawApiUrl?: string): string => {
  const apiUrl = getApiBaseUrl(rawApiUrl);

  try {
    const url = new URL(apiUrl);
    const isSecure = url.protocol === "https:" || url.protocol === "wss:";
    url.protocol = isSecure ? "wss:" : "ws:";
    if (shouldUpgradeToWss(url.hostname, url.protocol)) {
      url.protocol = "wss:";
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    return apiUrl.replace(/^http/, "ws").replace(/\/$/, "");
  }
};
