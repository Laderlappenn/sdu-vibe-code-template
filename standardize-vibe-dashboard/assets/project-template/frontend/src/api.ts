const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export type MetaTable = {
  name: string;
  total_rows: number | null;
  total_bytes: number | null;
};

export type MetaResponse = {
  sourceTables: string[];
  tables: MetaTable[];
};

export type SummaryResponse = {
  sourceTables: string[];
  tableCount: number;
  tables: string[];
};

export function getMeta() {
  return request<MetaResponse>("/meta");
}

export function getSummary() {
  return request<SummaryResponse>("/dashboard/summary");
}
