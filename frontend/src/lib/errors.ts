import axios from 'axios';

export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg ?? String(d)).join(', ');
    }
    if (err.response?.status === 0 || !err.response) {
      return 'Cannot reach server. Make sure the backend is running.';
    }
    return `Server error (${err.response?.status ?? 'unknown'})`;
  }
  if (err instanceof Error) return err.message;
  return 'An unexpected error occurred.';
}
