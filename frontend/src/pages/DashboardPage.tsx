import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ticketsApi } from '../lib/api';
import type { Ticket } from '../types/api';
import { getApiErrorMessage } from '../lib/errors';
import { statusBadge, priorityBadge } from '../components/badges';

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm text-slate-500 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    ticketsApi
      .list()
      .then(setTickets)
      .catch((e) => setError(getApiErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  const open = tickets.filter((t) => t.status === 'OPEN').length;
  const escalated = tickets.filter((t) => t.status === 'ESCALATED').length;
  const resolved = tickets.filter((t) =>
    ['RESOLVED', 'CLOSED'].includes(t.status)
  ).length;

  const recent = [...tickets]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome back, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Here's a summary of your support activity.
        </p>
      </div>

      {/* Quick actions */}
      <div className="flex flex-wrap gap-3 mb-8">
        <Link
          to="/chat"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Start a Chat
        </Link>
        <Link
          to="/tickets"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-50 transition-colors"
        >
          View Tickets
        </Link>
        <Link
          to="/knowledge"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-50 transition-colors"
        >
          Search Knowledge Base
        </Link>
      </div>

      {/* Stats */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-3/4 mb-3" />
              <div className="h-8 bg-slate-200 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Tickets" value={tickets.length} color="text-slate-900" />
          <StatCard label="Open" value={open} color="text-yellow-600" />
          <StatCard label="Escalated" value={escalated} color="text-red-600" />
          <StatCard label="Resolved" value={resolved} color="text-green-600" />
        </div>
      )}

      {/* Recent tickets */}
      <div className="bg-white rounded-xl border border-slate-200">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Recent Tickets</h2>
          <Link to="/tickets" className="text-sm text-blue-600 hover:underline">
            View all
          </Link>
        </div>

        {error && (
          <div className="p-5 text-red-600 text-sm">{error}</div>
        )}

        {!loading && !error && recent.length === 0 && (
          <div className="p-8 text-center text-slate-400 text-sm">
            No tickets yet.{' '}
            <Link to="/chat" className="text-blue-600 hover:underline">
              Start a chat
            </Link>{' '}
            to create one.
          </div>
        )}

        {recent.length > 0 && (
          <div className="divide-y divide-slate-100">
            {recent.map((t) => (
              <div key={t.id} className="px-5 py-3 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-mono text-slate-400">{t.ticket_number}</span>
                    {priorityBadge(t.priority)}
                  </div>
                  <p className="text-sm font-medium text-slate-900 truncate">{t.subject}</p>
                </div>
                <div className="flex-shrink-0">{statusBadge(t.status)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
