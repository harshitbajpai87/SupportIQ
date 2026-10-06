import React, { useEffect, useState } from 'react';
import { ticketsApi } from '../lib/api';
import type { Ticket, TicketCreate, TicketPriority } from '../types/api';
import { getApiErrorMessage } from '../lib/errors';
import { statusBadge, priorityBadge } from '../components/badges';

function CreateTicketModal({
  onCreated,
  onCancel,
}: {
  onCreated: (t: Ticket) => void;
  onCancel: () => void;
}) {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<TicketPriority>('MEDIUM');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data: TicketCreate = { subject, description, priority };
      const ticket = await ticketsApi.create(data);
      onCreated(ticket);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">New Support Ticket</h2>
        {error && (
          <div className="mb-3 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Subject</label>
            <input
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              required
              placeholder="Briefly describe your issue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              placeholder="Provide details about your issue…"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
            <select
              className="w-full text-sm border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={priority}
              onChange={(e) => setPriority(e.target.value as TicketPriority)}
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Creating…' : 'Create Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TicketRow({ ticket }: { ticket: Ticket }) {
  return (
    <div className="px-5 py-4 hover:bg-slate-50 transition-colors">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="font-mono text-xs text-slate-400">{ticket.ticket_number}</span>
            {priorityBadge(ticket.priority)}
            {ticket.detected_intent && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200">
                {ticket.detected_intent.replace(/_/g, ' ')}
              </span>
            )}
          </div>
          <p className="text-sm font-semibold text-slate-900 mb-0.5">{ticket.subject}</p>
          <p className="text-xs text-slate-500 line-clamp-2">{ticket.description}</p>
          {ticket.escalation_reason && (
            <p className="text-xs text-red-600 mt-1">⚠ {ticket.escalation_reason}</p>
          )}
          <p className="text-xs text-slate-400 mt-1">
            {new Date(ticket.created_at).toLocaleString()}
          </p>
        </div>
        <div className="flex-shrink-0 mt-0.5">{statusBadge(ticket.status)}</div>
      </div>
    </div>
  );
}

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [filter, setFilter] = useState<string>('ALL');

  const load = () => {
    setLoading(true);
    ticketsApi
      .list()
      .then((data) => setTickets(data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())))
      .catch((e) => setError(getApiErrorMessage(e)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const filtered =
    filter === 'ALL' ? tickets : tickets.filter((t) => t.status === filter);

  const handleCreated = (t: Ticket) => {
    setTickets((prev) => [t, ...prev]);
    setShowCreate(false);
    setSuccessMsg(`Ticket ${t.ticket_number} created successfully.`);
    setTimeout(() => setSuccessMsg(''), 5000);
  };

  const statusOptions = [
    'ALL', 'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'ESCALATED', 'RESOLVED', 'CLOSED',
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Support Tickets</h1>
          <p className="text-slate-500 text-sm mt-1">{tickets.length} total</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
        >
          + New Ticket
        </button>
      </div>

      {successMsg && (
        <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm">
          ✓ {successMsg}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap mb-4">
        {statusOptions.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              filter === s
                ? 'bg-blue-600 text-white border-blue-600'
                : 'border-slate-300 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {s === 'ALL' ? 'All' : s.replace(/_/g, ' ')}
            {s !== 'ALL' && (
              <span className="ml-1 opacity-75">
                ({tickets.filter((t) => t.status === s).length})
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        {loading && (
          <div className="p-8 text-center">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        )}
        {error && <div className="p-5 text-red-600 text-sm">{error}</div>}
        {!loading && filtered.length === 0 && (
          <div className="p-8 text-center text-slate-400 text-sm">
            No tickets found for this filter.
          </div>
        )}
        {filtered.map((t) => (
          <TicketRow key={t.id} ticket={t} />
        ))}
      </div>

      {showCreate && (
        <CreateTicketModal onCreated={handleCreated} onCancel={() => setShowCreate(false)} />
      )}
    </div>
  );
}
