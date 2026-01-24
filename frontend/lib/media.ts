import { getApiBaseUrl } from "@/shared/utils/url";

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

  const base = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);
  const path = value.startsWith("/") ? value : `/${value}`;
  return `${base}${path}`;
};
