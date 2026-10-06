// ─── API Types ──────────────────────────────────────────────────────────────

export type UserRole = 'CUSTOMER' | 'AGENT' | 'ADMIN';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  preferred_language: string;
  is_active: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  preferred_language?: string;
}

// ─── Chat ───────────────────────────────────────────────────────────────────

export type ConversationStatus = 'ACTIVE' | 'CLOSED' | 'ESCALATED';
export type MessageSender = 'USER' | 'BOT' | 'AGENT';

export interface IntentPrediction {
  intent: string;
  confidence: number;
  sentiment: string | null;
  sentiment_score: number | null;
  alternative_intents: Array<{ intent: string; confidence: number }> | null;
  entities: Record<string, string[]> | null;
  is_fallback: boolean;
}

export interface Message {
  id: number;
  conversation_id: string;
  sender: MessageSender;
  content: string;
  created_at: string;
  intent_prediction?: IntentPrediction | null;
}

export interface Conversation {
  id: string;
  user_id: number;
  title: string;
  status: ConversationStatus;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  status: ConversationStatus;
  created_at: string;
  updated_at: string;
}

export interface ChatResponse {
  user_message: Message;
  bot_message: Message;
  intent: string;
  confidence: number;
  sentiment: string;
  sentiment_score: number;
  escalated: boolean;
  escalation_reason: string | null;
  response_template: string;
}

// ─── Tickets ─────────────────────────────────────────────────────────────────

export type TicketStatus =
  | 'OPEN'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'WAITING_FOR_CUSTOMER'
  | 'RESOLVED'
  | 'CLOSED'
  | 'ESCALATED';

export type TicketPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface Ticket {
  id: number;
  ticket_number: string;
  user_id: number;
  conversation_id: string | null;
  subject: string;
  description: string;
  detected_intent: string | null;
  sentiment: string | null;
  priority: TicketPriority;
  status: TicketStatus;
  assigned_agent_id: number | null;
  escalation_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketCreate {
  subject: string;
  description: string;
  conversation_id?: string;
  priority?: TicketPriority;
}

export interface TicketUpdate {
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_agent_id?: number;
  escalation_reason?: string;
}

// ─── Knowledge ───────────────────────────────────────────────────────────────

export interface KnowledgeDocument {
  id: number;
  title: string;
  category: string;
  content: string;
  source: string | null;
  tags: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ─── Admin ───────────────────────────────────────────────────────────────────

export interface AdminStats {
  total_users: number;
  total_tickets: number;
  open_tickets: number;
  escalated_tickets: number;
}
