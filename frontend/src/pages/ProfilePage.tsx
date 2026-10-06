import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const roleBadgeColors: Record<string, string> = {
  ADMIN: 'bg-purple-100 text-purple-700 border-purple-200',
  AGENT: 'bg-blue-100 text-blue-700 border-blue-200',
  CUSTOMER: 'bg-slate-100 text-slate-600 border-slate-200',
};

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div className="p-6 max-w-xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Profile</h1>
        <p className="text-slate-500 text-sm mt-1">Your account information.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        {/* Avatar banner */}
        <div className="h-20 bg-gradient-to-r from-blue-500 to-blue-600" />
        <div className="px-6 pb-6">
          <div className="-mt-10 mb-4">
            <div className="w-20 h-20 rounded-full bg-white border-4 border-white shadow-sm bg-blue-100 flex items-center justify-center">
              <span className="text-blue-700 font-bold text-3xl">
                {user.name.charAt(0).toUpperCase()}
              </span>
            </div>
          </div>

          <h2 className="text-xl font-bold text-slate-900 mb-1">{user.name}</h2>
          <p className="text-slate-500 text-sm mb-3">{user.email}</p>

          <div className="flex items-center gap-2 mb-6">
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${
                roleBadgeColors[user.role]
              }`}
            >
              {user.role}
            </span>
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
                user.is_active
                  ? 'bg-green-50 text-green-700 border-green-200'
                  : 'bg-red-50 text-red-700 border-red-200'
              }`}
            >
              {user.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          <div className="space-y-3 border-t border-slate-100 pt-4">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">User ID</span>
              <span className="font-mono text-slate-700">#{user.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Email</span>
              <span className="text-slate-700">{user.email}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Language</span>
              <span className="text-slate-700">{user.preferred_language.toUpperCase()}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Role</span>
              <span className="text-slate-700">{user.role}</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100">
            <button
              onClick={handleLogout}
              className="w-full py-2.5 rounded-lg border border-red-300 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
