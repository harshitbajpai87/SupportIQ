import axios from 'axios';
import type {
  Token,
  LoginRequest,
  RegisterRequest,
  User,
  Conversation,
  ConversationSummary,
  ChatResponse,
  Ticket,
  TicketCreate,
  TicketUpdate,
  KnowledgeDocument,
  AdminStats,
} from '../types/api';

// ─── Axios instance ──────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global 401 → clear session (token expired / invalid)
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      // Let components handle the redirect via AuthContext
    }
    return Promise.reject(err);
  }
);

export default api;

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<Token>('/auth/login', data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    api.post<User>('/auth/register', data).then((r) => r.data),

  me: () => api.get<User>('/auth/me').then((r) => r.data),
};

// ─── Chat ────────────────────────────────────────────────────────────────────

export const chatApi = {
  createConversation: (title?: string) =>
    api
      .post<Conversation>('/chat/conversations', { title: title ?? 'New Conversation' })
      .then((r) => r.data),

  listConversations: () =>
    api.get<ConversationSummary[]>('/chat/conversations').then((r) => r.data),

  getConversation: (id: string) =>
    api.get<Conversation>(`/chat/conversations/${id}`).then((r) => r.data),

  closeConversation: (id: string) =>
    api.delete(`/chat/conversations/${id}`).then((r) => r.data),

  sendMessage: (conversation_id: string, message: string) =>
    api
      .post<ChatResponse>('/chat/message', { conversation_id, message })
      .then((r) => r.data),
};

// ─── Tickets ─────────────────────────────────────────────────────────────────

export const ticketsApi = {
  list: () => api.get<Ticket[]>('/tickets').then((r) => r.data),

  get: (id: number) => api.get<Ticket>(`/tickets/${id}`).then((r) => r.data),

  create: (data: TicketCreate) =>
    api.post<Ticket>('/tickets', data).then((r) => r.data),

  update: (id: number, data: TicketUpdate) =>
    api.patch<Ticket>(`/tickets/${id}`, data).then((r) => r.data),
};

// ─── Knowledge ───────────────────────────────────────────────────────────────

export const knowledgeApi = {
  list: () =>
    api.get<KnowledgeDocument[]>('/knowledge').then((r) => r.data),

  search: (q: string) =>
    api.get<KnowledgeDocument[]>('/knowledge/search', { params: { q } }).then((r) => r.data),

  get: (id: number) =>
    api.get<KnowledgeDocument>(`/knowledge/${id}`).then((r) => r.data),
};

// ─── Admin ───────────────────────────────────────────────────────────────────

export const adminApi = {
  stats: () => api.get<AdminStats>('/admin/stats').then((r) => r.data),

  listUsers: () => api.get<User[]>('/admin/users').then((r) => r.data),

  updateUserRole: (userId: number, role: string) =>
    api
      .patch<User>(`/admin/users/${userId}`, null, { params: { role } })
      .then((r) => r.data),
};
