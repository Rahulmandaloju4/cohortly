import React, { useState, useRef, useEffect } from 'react';
import { useRole, DemoRole, ROLE_DEFINITIONS } from '../../context/RoleContext';
import { UserCheck, Shield, ChevronDown, Check, Info, Bell, RefreshCw } from 'lucide-react';

export const Header: React.FC = () => {
  const { role, roleInfo, setRole } = useRole();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const rolesList: DemoRole[] = [
    'PLATFORM_ADMIN',
    'ACADEMIC_ADMIN',
    'INSTRUCTOR',
    'SUPPORT_STAFF',
    'LEARNER',
  ];

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm shadow-slate-100">
      {/* Platform Title & Tagline */}
      <div className="flex items-center space-x-4">
        <div>
          <h1 className="text-base font-semibold text-slate-800 leading-tight">
            Cohortly Intelligence Workspace
          </h1>
          <p className="text-xs text-slate-400">
            "Turn learning data into actionable intelligence."
          </p>
        </div>
      </div>

      {/* Right Controls: Role Switcher & System Indicators */}
      <div className="flex items-center space-x-4">
        {/* Role Switcher Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center space-x-2.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50/80 hover:bg-slate-100/80 transition-all text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <div className="w-5 h-5 rounded-md bg-blue-600/10 text-blue-600 flex items-center justify-center font-bold">
              <UserCheck className="w-3.5 h-3.5" />
            </div>
            <div className="text-left">
              <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                Demo Role
              </div>
              <div className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                {roleInfo.title}
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold border ${roleInfo.color}`}>
                  {roleInfo.badge}
                </span>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="px-3 py-2 border-b border-slate-100">
                <div className="text-xs font-semibold text-slate-800">Switch Demo Role (X-Demo-Role)</div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Simulates full-stack RBAC across API routes and page controls.
                </p>
              </div>

              <div className="py-1">
                {rolesList.map((r) => {
                  const info = ROLE_DEFINITIONS[r];
                  const isSelected = r === role;
                  return (
                    <button
                      key={r}
                      onClick={() => {
                        setRole(r);
                        setDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2.5 text-xs flex items-start space-x-2.5 transition-colors ${
                        isSelected ? 'bg-blue-50/70 text-blue-900 font-medium' : 'hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      <div className="mt-0.5 flex-shrink-0">
                        {isSelected ? (
                          <Check className="w-4 h-4 text-blue-600" />
                        ) : (
                          <div className="w-4 h-4 rounded-full border border-slate-300" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-800">{info.title}</span>
                          <span className={`text-[10px] px-1.5 py-0.2 rounded font-medium border ${info.color}`}>
                            {info.badge}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                          {info.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="px-3 py-2 bg-slate-50/80 border-t border-slate-100 text-[10px] text-slate-500 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                <span>Header applied on every REST query.</span>
              </div>
            </div>
          )}
        </div>

        {/* Global Evaluation Anchor Date Badge */}
        <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 text-xs border border-slate-200">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Anchor:</span>
          <span className="font-mono font-medium text-slate-800">2026-10-22</span>
        </div>
      </div>
    </header>
  );
};
