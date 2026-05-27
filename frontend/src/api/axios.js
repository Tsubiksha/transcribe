import axios from "axios";

const fallbackBaseUrl =
  window.location.port === "5173" ? "http://127.0.0.1:8000" : window.location.origin;

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || fallbackBaseUrl,
  timeout: 120000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.dispatchEvent(new Event("auth:logout"));
    }
    return Promise.reject(error);
  }
);

export function getApiErrorMessage(error, fallback = "Request failed") {
  if (error.code === "ECONNABORTED") {
    return "The request timed out while processing. Longer media can take a long time to download, transcribe, and index. Please try a shorter video or upload the audio/video file directly.";
  }
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join(" ");
  }
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return error.message || fallback;
}

export default api;
