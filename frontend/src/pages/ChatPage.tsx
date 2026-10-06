import React, { useEffect, useRef, useState } from 'react';
import { chatApi, ticketsApi } from '../lib/api';
import type {
  Conversation,
  ConversationSummary,
  Message,
  ChatResponse,
} from '../types/api';
import { getApiErrorMessage } from '../lib/errors';

// ─── Sub-components ──────────────────────────────────────────────────────────

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 w-8 text-right">{pct}%</span>
    </div>
  );
}

function MLBadge({ response }: { response: ChatResponse }) {
  const { intent, confidence, sentiment, escalated, escalation_reason } = response;

  return (
    <div className="mt-1 mx-3 mb-3 rounded-lg bg-slate-50 border border-slate-200 p-3 text-xs space-y-1.5">
      <div className="flex flex-wrap gap-3 items-start">
        <div className="min-w-0">
          <span className="text-slate-500">Intent: </span>
          <span className="font-mono font-medium text-slate-800">{intent}</span>
        </div>
        <div className="min-w-0">
          <span className="text-slate-500">Sentiment: </span>
          <span
            className={`font-medium ${
              sentiment === 'positive'
                ? 'text-green-600'
                : sentiment === 'negative'
                ? 'text-red-600'
                : 'text-slate-600'
            }`}
          >
            {sentiment}
          </span>
        </div>
      </div>
      <div>
        <span className="text-slate-500 block mb-1">Confidence:</span>
        <ConfidenceMeter value={confidence} />
      </div>
      {escalated && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-red-700">
          <span className="font-semibold">⚠ Escalated — </span>
          {escalation_reason}
        </div>
      )}
    </div>
  );
}

function MessageBubble({
  msg,
  mlResponse,
}: {
  msg: Message;
  mlResponse?: ChatResponse;
}) {
  const isUser = msg.sender === 'USER';
  const time = new Date(msg.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] ${isUser ? '' : 'w-full'}`}>
        {/* Avatar label */}
        <div
          className={`flex items-center gap-1 mb-1 ${isUser ? 'justify-end' : 'justify-start'}`}
        >
          <span className="text-xs text-slate-400">
            {isUser ? 'You' : 'SupportIQ Bot'} · {time}
          </span>
        </div>

        {/* Bubble */}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-sm'
              : 'bg-white border border-slate-200 text-slate-900 rounded-bl-sm'
          }`}
        >
          {msg.content}
        </div>

        {/* ML details — only on bot messages with associated response */}
        {!isUser && mlResponse && <MLBadge response={mlResponse} />}
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex justify-start">
      <div className="max-w-[75%]">
        <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-white border border-slate-200">
          <div className="flex gap-1 items-center">
            <span className="w-2 h-2 rounded-full bg-slate-300 animate-bounce [animation-delay:-0.3s]" />
            <span className="w-2 h-2 rounded-full bg-slate-300 animate-bounce [animation-delay:-0.15s]" />
            <span className="w-2 h-2 rounded-full bg-slate-300 animate-bounce" />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Ticket creation panel ────────────────────────────────────────────────────

function CreateTicketPanel({
  conversationId,
  onCreated,
  onCancel,
}: {
  conversationId: string;
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'>('MEDIUM');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await ticketsApi.create({ subject, description, conversation_id: conversationId, priority });
      onCreated();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-800 mb-3">Create Support Ticket</h3>
      {error && <p className="text-red-600 text-xs mb-2">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-2">
        <input
          className="w-full text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          required
        />
        <textarea
          className="w-full text-sm border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          rows={2}
          placeholder="Describe your issue…"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
        <div className="flex items-center gap-2">
          <select
            className="text-sm border border-slate-300 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={priority}
            onChange={(e) => setPriority(e.target.value as typeof priority)}
          >
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
          <div className="flex gap-2 ml-auto">
            <button
              type="button"
              onClick={onCancel}
              className="text-sm px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="text-sm px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Creating…' : 'Create Ticket'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function ChatPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [activeConv, setActiveConv] = useState<Conversation | null>(null);
  const [mlResponses, setMlResponses] = useState<Record<number, ChatResponse>>({});
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [showTicketForm, setShowTicketForm] = useState(false);
  const [ticketSuccess, setTicketSuccess] = useState(false);
  const [convsError, setConvsError] = useState('');
  const [sendError, setSendError] = useState('');

  const bottomRef = useRef<HTMLDivElement>(null);

  // Load conversation list
  useEffect(() => {
    chatApi
      .listConversations()
      .then(setConversations)
      .catch((e) => setConvsError(getApiErrorMessage(e)))
      .finally(() => setLoadingConvs(false));
  }, []);

  // Load active conversation messages
  useEffect(() => {
    if (!activeConvId) return;
    setLoadingMsgs(true);
    setActiveConv(null);
    chatApi
      .getConversation(activeConvId)
      .then(setActiveConv)
      .catch(() => setActiveConv(null))
      .finally(() => setLoadingMsgs(false));
  }, [activeConvId]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConv?.messages, sending]);

  const startNewConversation = async () => {
    try {
      const conv = await chatApi.createConversation();
      setConversations((prev) => [conv, ...prev]);
      setActiveConvId(conv.id);
      setTicketSuccess(false);
      setShowTicketForm(false);
    } catch (e) {
      setConvsError(getApiErrorMessage(e));
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || !activeConvId || sending) return;

    setInput('');
    setSendError('');
    setSending(true);

    try {
      const response = await chatApi.sendMessage(activeConvId, text);

      // Update active conversation messages
      setActiveConv((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          status: response.escalated ? 'ESCALATED' : prev.status,
          messages: [...prev.messages, response.user_message, response.bot_message],
        };
      });

      // Store ML metadata keyed by BOT message id
      setMlResponses((prev) => ({
        ...prev,
        [response.bot_message.id]: response,
      }));

      // Update conversation list (status + updated_at)
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConvId
            ? { ...c, status: response.escalated ? 'ESCALATED' : c.status }
            : c
        )
      );
    } catch (err) {
      setSendError(getApiErrorMessage(err));
    } finally {
      setSending(false);
    }
  };

  const messages: Message[] = activeConv?.messages ?? [];

  const statusColor: Record<string, string> = {
    ACTIVE: 'bg-green-400',
    ESCALATED: 'bg-red-400',
    CLOSED: 'bg-slate-300',
  };

  return (
    <div className="flex h-full">
      {/* Conversation list */}
      <div className="hidden sm:flex w-64 flex-col flex-shrink-0 bg-white border-r border-slate-200">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-800 text-sm">Conversations</h2>
          <button
            onClick={startNewConversation}
            className="text-xs px-2.5 py-1 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
            aria-label="New conversation"
          >
            + New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {loadingConvs && (
            <div className="p-4 space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 rounded-lg bg-slate-100 animate-pulse" />
              ))}
            </div>
          )}
          {convsError && <p className="p-4 text-red-600 text-xs">{convsError}</p>}
          {!loadingConvs && conversations.length === 0 && (
            <p className="p-4 text-slate-400 text-xs">No conversations yet. Start one!</p>
          )}
          {conversations.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                setActiveConvId(c.id);
                setShowTicketForm(false);
                setTicketSuccess(false);
              }}
              className={`w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 transition-colors ${
                activeConvId === c.id ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    statusColor[c.status] ?? 'bg-slate-300'
                  }`}
                />
                <span className="text-sm font-medium text-slate-800 truncate flex-1">
                  {c.title}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 pl-4">
                {new Date(c.updated_at).toLocaleDateString()}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {!activeConvId ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-blue-100 flex items-center justify-center mb-4">
              <span className="text-2xl">💬</span>
            </div>
            <h2 className="text-lg font-semibold text-slate-800 mb-2">
              No conversation selected
            </h2>
            <p className="text-slate-500 text-sm mb-4">
              Select a conversation or start a new one.
            </p>
            <button
              onClick={startNewConversation}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
            >
              Start New Conversation
            </button>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="px-4 py-3 bg-white border-b border-slate-200 flex items-center gap-3">
              {/* Mobile: back button */}
              <button
                className="sm:hidden text-slate-500 hover:text-slate-700 text-sm"
                onClick={() => setActiveConvId(null)}
              >
                ←
              </button>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-900 text-sm truncate">
                  {activeConv?.title ?? 'Loading…'}
                </p>
                {activeConv && (
                  <p
                    className={`text-xs ${
                      activeConv.status === 'ESCALATED' ? 'text-red-600' : 'text-slate-400'
                    }`}
                  >
                    {activeConv.status}
                  </p>
                )}
              </div>
              <button
                onClick={() => {
                  setShowTicketForm((v) => !v);
                  setTicketSuccess(false);
                }}
                className="text-xs px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50"
              >
                Create Ticket
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-3 bg-slate-50">
              {loadingMsgs && (
                <div className="flex justify-center py-8">
                  <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}

              {!loadingMsgs && messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center py-12">
                  <p className="text-slate-400 text-sm">
                    No messages yet. Say hello to get started!
                  </p>
                </div>
              )}

              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  msg={msg}
                  mlResponse={msg.sender === 'BOT' ? mlResponses[msg.id] : undefined}
                />
              ))}

              {sending && <Spinner />}
              <div ref={bottomRef} />
            </div>

            {/* Send error */}
            {sendError && (
              <div className="px-4 py-2 bg-red-50 border-t border-red-200">
                <p className="text-red-600 text-xs">{sendError}</p>
              </div>
            )}

            {/* Ticket form */}
            {showTicketForm && activeConvId && (
              <CreateTicketPanel
                conversationId={activeConvId}
                onCreated={() => {
                  setShowTicketForm(false);
                  setTicketSuccess(true);
                }}
                onCancel={() => setShowTicketForm(false)}
              />
            )}

            {ticketSuccess && (
              <div className="px-4 py-2 bg-green-50 border-t border-green-200">
                <p className="text-green-700 text-xs font-medium">
                  ✓ Ticket created successfully.{' '}
                  <a href="/tickets" className="underline">
                    View in Tickets
                  </a>
                </p>
              </div>
            )}

            {/* Input */}
            {activeConv?.status !== 'CLOSED' && (
              <form
                onSubmit={sendMessage}
                className="px-4 py-3 bg-white border-t border-slate-200 flex gap-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={
                    activeConv?.status === 'ESCALATED'
                      ? 'Escalated — an agent will follow up…'
                      : 'Type a message…'
                  }
                  disabled={sending}
                  className="flex-1 text-sm px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-50"
                  aria-label="Message input"
                />
                <button
                  type="submit"
                  disabled={sending || !input.trim()}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Send
                </button>
              </form>
            )}
            {activeConv?.status === 'CLOSED' && (
              <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 text-center text-sm text-slate-500">
                This conversation is closed.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
