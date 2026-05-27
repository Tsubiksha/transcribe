import api, { getApiErrorMessage } from "./axios";

export async function processYouTubeUrl(url) {
  try {
    const { data } = await api.post("/api/youtube/process", { url }, { timeout: 120000 });
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Could not start YouTube processing"));
  }
}

export async function fetchYouTubeMetadata(url) {
  try {
    const { data } = await api.post("/api/youtube/metadata", { url }, { timeout: 120000 });
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Could not fetch YouTube metadata"));
  }
}

export function formatDuration(seconds) {
  if (!seconds) return "Ready for processing";
  const total = Math.round(seconds);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  if (hours) return `${hours}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

export async function listYouTubeSources() {
  const { data } = await api.get("/api/sources");
  return data.filter((item) => item.source_type === "youtube");
}
