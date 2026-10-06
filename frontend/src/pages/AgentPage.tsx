import { useEffect, useState } from 'react';
import { ticketsApi } from '../lib/api';
import type { Ticket, TicketStatus, TicketUpdate } from '../types/api';
import { getApiErrorMessage } from '../lib/errors';
import { statusBadge, priorityBadge, sentimentBadge } from '../components/badges';

const AGENT_STATUSES: TicketStatus[] = [
  'ASSIGNED',
  'IN_PROGRESS',
  'WAITING_FOR_CUSTOMER',
  'RESOLVED',
  'CLOSED',
];

function TicketCard({
  ticket,
  onUpdated,
}: {
  ticket: Ticket;
  onUpdated: (t: Ticket) => void;
}) {
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');

  const updateStatus = async (status: TicketStatus) => {
    setUpdating(true);
    setError('');
    try {
      const data: TicketUpdate = { status };
      const updated = await ticketsApi.update(ticket.id, data);
      onUpdated(updated);
    } catch (e) {
      setError(getApiErrorMessage(e));
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="font-mono text-xs text-slate-400">{ticket.ticket_number}</span>
            {priorityBadge(ticket.priority)}
            {statusBadge(ticket.status)}
          </div>
          <h3 className="font-semibold text-slate-900 text-sm">{ticket.subject}</h3>
        </div>
      </div>

      <p className="text-sm text-slate-600 mb-3 line-clamp-3">{ticket.description}</p>

      {/* ML metadata */}
      {(ticket.detected_intent || ticket.sentiment) && (
        <div className="flex flex-wrap gap-2 mb-3">
          {ticket.detected_intent && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200">
              {ticket.detected_intent.replace(/_/g, ' ')}
            </span>
          )}
          {sentimentBadge(ticket.sentiment)}
        </div>
      )}

      {ticket.escalation_reason && (
        <div className="mb-3 p-2 rounded-lg bg-red-50 border border-red-200">
          <p className="text-xs text-red-700">
            <span className="font-semibold">⚠ Escalation: </span>
            {ticket.escalation_reason}
          </p>
        </div>
      )}

      <p className="text-xs text-slate-400 mb-3">
        {new Date(ticket.created_at).toLocaleString()}
      </p>

      {error && <p className="text-xs text-red-600 mb-2">{error}</p>}

      {/* Status update */}
      <div className="flex flex-wrap gap-2">
        {AGENT_STATUSES.filter((s) => s !== ticket.status).map((s) => (
          <button
            key={s}
            onClick={() => updateStatus(s)}
            disabled={updating}
            className="text-xs px-2.5 py-1 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition-colors"
          >
            → {s.replace(/_/g, ' ')}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function AgentPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'assigned' | 'escalated'>('assigned');

  useEffect(() => {
    ticketsApi
      .list()
      .then((data) =>
        setTickets(data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()))
      )
      .catch((e) => setError(getApiErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  const handleUpdated = (updated: Ticket) => {
    setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  };

  const assigned = tickets.filter(
    (t) => ['ASSIGNED', 'IN_PROGRESS', 'WAITING_FOR_CUSTOMER'].includes(t.status)
  );
  const escalated = tickets.filter((t) => t.status === 'ESCALATED');

  const displayed = tab === 'assigned' ? assigned : escalated;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Agent Queue</h1>
        <p className="text-slate-500 text-sm mt-1">
          Manage assigned and escalated tickets.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-100 rounded-lg p-1 w-fit">
        {(
          [
            { id: 'assigned', label: `Assigned (${assigned.length})` },
            { id: 'escalated', label: `Escalated (${escalated.length})` },
          ] as const
        ).map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              tab === id
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-slate-200 rounded w-full mb-1" />
              <div className="h-3 bg-slate-200 rounded w-5/6" />
            </div>
          ))}
        </div>
      )}

      {!loading && displayed.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <p className="text-base font-medium mb-1">
            {tab === 'assigned' ? 'No assigned tickets' : 'No escalated tickets'}
          </p>
          <p className="text-sm">Check back later.</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {displayed.map((t) => (
          <TicketCard key={t.id} ticket={t} onUpdated={handleUpdated} />
        ))}
      </div>
    </div>
  );
}
