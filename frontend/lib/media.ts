export const resolveAssetUrl = (value?: string | null): string => {
  if (!value) return "";
  if (
    value.startsWith("http://") ||
    value.startsWith("https://") ||
    value.startsWith("blob:") ||
    value.startsWith("data:")
  ) {
    return value;
  }

  const base = (process.env.NEXT_PUBLIC_API_URL || "https://api.valsa.solutions").replace(/\/+$/, "");
  const path = value.startsWith("/") ? value : `/${value}`;
  return `${base}${path}`;
};
