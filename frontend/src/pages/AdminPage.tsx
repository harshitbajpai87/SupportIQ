import { useEffect, useState } from 'react';
import { adminApi } from '../lib/api';
import type { AdminStats, User } from '../types/api';
import { getApiErrorMessage } from '../lib/errors';

function StatCard({
  label,
  value,
  color,
  description,
}: {
  label: string;
  value: number;
  color: string;
  description?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-sm text-slate-500 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color} mb-1`}>{value}</p>
      {description && <p className="text-xs text-slate-400">{description}</p>}
    </div>
  );
}

const roleBadge = (role: string) => {
  const colors: Record<string, string> = {
    ADMIN: 'bg-purple-100 text-purple-700 border-purple-200',
    AGENT: 'bg-blue-100 text-blue-700 border-blue-200',
    CUSTOMER: 'bg-slate-100 text-slate-600 border-slate-200',
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
        colors[role] ?? colors.CUSTOMER
      }`}
    >
      {role}
    </span>
  );
};

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [statsLoading, setStatsLoading] = useState(true);
  const [usersLoading, setUsersLoading] = useState(true);
  const [statsError, setStatsError] = useState('');
  const [usersError, setUsersError] = useState('');
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [roleError, setRoleError] = useState('');
  const [tab, setTab] = useState<'stats' | 'users'>('stats');

  useEffect(() => {
    adminApi
      .stats()
      .then(setStats)
      .catch((e) => setStatsError(getApiErrorMessage(e)))
      .finally(() => setStatsLoading(false));

    adminApi
      .listUsers()
      .then(setUsers)
      .catch((e) => setUsersError(getApiErrorMessage(e)))
      .finally(() => setUsersLoading(false));
  }, []);

  const updateRole = async (userId: number, role: string) => {
    setUpdatingId(userId);
    setRoleError('');
    try {
      const updated = await adminApi.updateUserRole(userId, role);
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    } catch (e) {
      setRoleError(getApiErrorMessage(e));
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">Platform-wide statistics and user management.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-100 rounded-lg p-1 w-fit">
        {(
          [
            { id: 'stats', label: 'Statistics' },
            { id: 'users', label: `Users (${users.length})` },
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

      {/* Stats tab */}
      {tab === 'stats' && (
        <>
          {statsError && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
              {statsError}
            </div>
          )}
          {statsLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="bg-white rounded-xl border border-slate-200 p-5 animate-pulse"
                >
                  <div className="h-3 bg-slate-200 rounded w-3/4 mb-3" />
                  <div className="h-8 bg-slate-200 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : stats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Total Users"
                value={stats.total_users}
                color="text-slate-900"
                description="All registered accounts"
              />
              <StatCard
                label="Total Tickets"
                value={stats.total_tickets}
                color="text-slate-900"
                description="All time"
              />
              <StatCard
                label="Open Tickets"
                value={stats.open_tickets}
                color="text-yellow-600"
                description="Awaiting action"
              />
              <StatCard
                label="Escalated"
                value={stats.escalated_tickets}
                color="text-red-600"
                description="Needs agent attention"
              />
            </div>
          ) : null}
        </>
      )}

      {/* Users tab */}
      {tab === 'users' && (
        <>
          {usersError && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
              {usersError}
            </div>
          )}
          {roleError && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
              {roleError}
            </div>
          )}

          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {usersLoading && (
              <div className="p-8 text-center">
                <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
              </div>
            )}
            {!usersLoading && users.length === 0 && (
              <div className="p-8 text-center text-slate-400 text-sm">No users found.</div>
            )}
            {users.map((u) => (
              <div key={u.id} className="px-5 py-4 flex items-center gap-4">
                <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-blue-700 font-semibold text-sm">
                    {u.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900">{u.name}</p>
                  <p className="text-xs text-slate-500">{u.email}</p>
                </div>
                <div className="flex items-center gap-3">
                  {roleBadge(u.role)}
                  <select
                    value={u.role}
                    disabled={updatingId === u.id}
                    onChange={(e) => updateRole(u.id, e.target.value)}
                    className="text-xs border border-slate-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    aria-label={`Change role for ${u.name}`}
                  >
                    <option value="CUSTOMER">CUSTOMER</option>
                    <option value="AGENT">AGENT</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                  {updatingId === u.id && (
                    <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
