import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  GraduationCap,
  BarChart3,
  AlertTriangle,
  Cpu,
  ShieldCheck,
  Sparkles,
  Database,
  Lock,
} from 'lucide-react';
import { useRole, DemoRole } from '../../context/RoleContext';

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
  allowedRoles: DemoRole[];
}

const NAV_ITEMS: NavItem[] = [
  {
    name: 'Overview Dashboard',
    path: '/',
    icon: LayoutDashboard,
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN', 'INSTRUCTOR', 'SUPPORT_STAFF', 'LEARNER'],
  },
  {
    name: 'Learners Directory',
    path: '/learners',
    icon: Users,
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN', 'INSTRUCTOR', 'SUPPORT_STAFF'],
  },
  {
    name: 'Courses & Curriculum',
    path: '/courses',
    icon: BookOpen,
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN', 'INSTRUCTOR', 'SUPPORT_STAFF', 'LEARNER'],
  },
  {
    name: 'Cohort Intelligence',
    path: '/cohorts',
    icon: GraduationCap,
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN', 'INSTRUCTOR', 'SUPPORT_STAFF'],
  },
  {
    name: 'Content Funnel',
    path: '/content',
    icon: BarChart3,
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN', 'INSTRUCTOR'],
  },
  {
    name: 'Exceptions & Triage',
    path: '/exceptions',
    icon: AlertTriangle,
    badge: 'Anomalies',
    badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN', 'INSTRUCTOR', 'SUPPORT_STAFF'],
  },
  {
    name: 'Synthetic Generator',
    path: '/generator',
    icon: Cpu,
    badge: 'Seed 20261022',
    badgeColor: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN'],
  },
  {
    name: 'Quality & Benchmark',
    path: '/audit',
    icon: ShieldCheck,
    badge: '15 Checks',
    badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    allowedRoles: ['PLATFORM_ADMIN', 'ACADEMIC_ADMIN'],
  },
];

export const Sidebar: React.FC = () => {
  const { role, roleInfo } = useRole();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0 min-h-screen text-slate-300 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 ring-1 ring-white/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
              Cohortly
              <span className="text-[10px] font-medium tracking-wide uppercase px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                v1.0
              </span>
            </span>
            <p className="text-[11px] text-slate-400 font-normal truncate mt-0.5">
              Learning Analytics & Intelligence
            </p>
          </div>
        </div>
      </div>

      {/* Role Context Chip */}
      <div className="px-4 py-3 bg-slate-950/40 border-b border-slate-800/60">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium">Active Demo Role:</span>
          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${roleInfo.color}`}>
            {roleInfo.badge}
          </span>
        </div>
        <p className="text-[11px] text-slate-400 mt-1 line-clamp-1 font-mono">
          {roleInfo.title}
        </p>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Platform Workspace
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isRestricted = item.allowedRoles && !item.allowedRoles.includes(role);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                  isActive
                    ? isRestricted
                      ? 'bg-slate-800 text-amber-300/90 border border-amber-500/20 shadow-sm font-semibold'
                      : 'bg-blue-600 text-white shadow-md shadow-blue-600/20 font-semibold'
                    : isRestricted
                    ? 'text-slate-400 hover:text-slate-300 hover:bg-slate-800/40'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center space-x-3 min-w-0">
                {isRestricted ? (
                  <Lock className="w-4 h-4 text-slate-400 flex-shrink-0 transition-transform group-hover:scale-110" />
                ) : (
                  <Icon className="w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110" />
                )}
                <span className={`truncate ${isRestricted ? 'text-slate-400 group-hover:text-slate-300' : ''}`}>
                  {item.name}
                </span>
              </div>
              {isRestricted ? (
                <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded border border-slate-700/60 bg-slate-800/60 text-slate-400 flex items-center gap-1">
                  Restricted
                </span>
              ) : (
                item.badge && (
                  <span
                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border tracking-tight ${
                      item.badgeColor || 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {item.badge}
                  </span>
                )
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Engine Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/60">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="flex items-center gap-1.5 text-slate-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Engine Active
          </span>
          <span className="text-[10px] font-mono text-slate-400">Seed: 20261022</span>
        </div>
        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800 text-[11px]">
          <span className="text-slate-400 flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            SQLite WAL Mode
          </span>
          <span className="text-emerald-400 font-mono font-semibold">Healthy</span>
        </div>
      </div>
    </aside>
  );
};
