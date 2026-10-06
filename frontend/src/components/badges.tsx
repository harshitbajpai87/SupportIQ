import type { TicketStatus, TicketPriority } from '../types/api';

const statusColors: Record<TicketStatus, string> = {
  OPEN: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  ASSIGNED: 'bg-blue-50 text-blue-700 border-blue-200',
  IN_PROGRESS: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  WAITING_FOR_CUSTOMER: 'bg-slate-50 text-slate-600 border-slate-200',
  RESOLVED: 'bg-green-50 text-green-700 border-green-200',
  CLOSED: 'bg-slate-50 text-slate-500 border-slate-200',
  ESCALATED: 'bg-red-50 text-red-700 border-red-200',
};

const priorityColors: Record<TicketPriority, string> = {
  LOW: 'bg-slate-50 text-slate-500 border-slate-200',
  MEDIUM: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  HIGH: 'bg-orange-50 text-orange-700 border-orange-200',
  CRITICAL: 'bg-red-50 text-red-700 border-red-200',
};

export function statusBadge(status: TicketStatus) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${statusColors[status]}`}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export function priorityBadge(priority: TicketPriority) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${priorityColors[priority]}`}
    >
      {priority}
    </span>
  );
}

export function sentimentBadge(sentiment: string | null) {
  if (!sentiment) return null;
  const colors: Record<string, string> = {
    positive: 'bg-green-50 text-green-700 border-green-200',
    negative: 'bg-red-50 text-red-700 border-red-200',
    neutral: 'bg-slate-50 text-slate-500 border-slate-200',
  };
  const cls = colors[sentiment.toLowerCase()] ?? 'bg-slate-50 text-slate-500 border-slate-200';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {sentiment}
    </span>
  );
}
