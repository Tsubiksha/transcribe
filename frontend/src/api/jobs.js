import api from "./axios";

export async function getJob(jobId) {
  const { data } = await api.get(`/api/jobs/${jobId}`, { timeout: 120000 });
  return data;
}

export async function listActiveJobs() {
  const { data } = await api.get("/api/jobs/active", { timeout: 120000 });
  return data;
}

export async function cancelJob(jobId) {
  const { data } = await api.post(`/api/jobs/${jobId}/cancel`, {}, { timeout: 120000 });
  return data;
}

export function isTerminalJob(job) {
  return ["completed", "failed", "cancelled"].includes(job?.status);
}
