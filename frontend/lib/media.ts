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

export type VideoPlatform = "youtube" | "vimeo" | "loom" | "wistia" | "vidyard" | "unknown";

export interface VideoInfo {
  platform: VideoPlatform;
  videoId: string;
  embedUrl: string;
  thumbnailUrl: string;
}

/**
 * Extract video information from URL
 */
export function getVideoInfo(url: string): VideoInfo | null {
  if (!url) return null;

  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();

    // YouTube
    if (hostname.includes("youtube.com") || hostname.includes("youtu.be")) {
      let videoId = "";
      
      if (hostname.includes("youtu.be")) {
        videoId = urlObj.pathname.slice(1);
      } else if (urlObj.pathname.includes("/embed/")) {
        videoId = urlObj.pathname.split("/embed/")[1].split("?")[0];
      } else if (urlObj.searchParams.has("v")) {
        videoId = urlObj.searchParams.get("v") || "";
      } else if (urlObj.pathname.includes("/watch/")) {
        videoId = urlObj.pathname.split("/watch/")[1].split("?")[0];
      }

      if (videoId) {
        return {
          platform: "youtube",
          videoId,
          embedUrl: `https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`,
          thumbnailUrl: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`,
        };
      }
    }

    // Vimeo
    if (hostname.includes("vimeo.com")) {
      const videoId = urlObj.pathname.split("/").filter(Boolean).pop() || "";
      if (videoId && !isNaN(Number(videoId))) {
        return {
          platform: "vimeo",
          videoId,
          embedUrl: `https://player.vimeo.com/video/${videoId}?title=0&byline=0&portrait=0`,
          thumbnailUrl: "", // Vimeo thumbnails require oEmbed API call
        };
      }
    }

    // Loom
    if (hostname.includes("loom.com")) {
      const videoId = urlObj.pathname.split("/").filter(Boolean).pop() || "";
      if (videoId) {
        return {
          platform: "loom",
          videoId,
          embedUrl: `https://www.loom.com/embed/${videoId}`,
          thumbnailUrl: `https://cdn.loom.com/sessions/thumbnails/${videoId}-00000000-0000-0000-0000-000000000000-00000-00000-00000-00000-with-play.gif`,
        };
      }
    }

    // Wistia
    if (hostname.includes("wistia.com")) {
      const videoId = urlObj.pathname.split("/").filter(Boolean).pop() || "";
      if (videoId) {
        return {
          platform: "wistia",
          videoId,
          embedUrl: `https://fast.wistia.net/embed/iframe/${videoId}`,
          thumbnailUrl: "", // Wistia requires API call for thumbnail
        };
      }
    }

    // Vidyard
    if (hostname.includes("vidyard.com")) {
      const videoId = urlObj.pathname.split("/").filter(Boolean).pop() || "";
      if (videoId) {
        return {
          platform: "vidyard",
          videoId,
          embedUrl: `https://play.vidyard.com/${videoId}`,
          thumbnailUrl: "", // Vidyard requires API call for thumbnail
        };
      }
    }

    return null;
  } catch {
    return null;
  }
}
