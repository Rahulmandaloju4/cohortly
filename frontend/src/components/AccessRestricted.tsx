import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, Shield } from 'lucide-react';
import { RESTRICTED_ACCESS_MESSAGE } from '../utils/errors';

interface AccessRestrictedProps {
  customMessage?: string;
}

export const AccessRestricted: React.FC<AccessRestrictedProps> = ({ customMessage }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] p-6 animate-in fade-in duration-200">
      <div className="max-w-lg w-full bg-white rounded-2xl border border-slate-200/90 shadow-sm p-8 text-center space-y-6">
        {/* Shield Icon with Warning Accent Badge */}
        <div className="mx-auto w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200/70 flex items-center justify-center text-amber-600 shadow-sm relative">
          <ShieldAlert className="w-8 h-8 text-amber-600" />
          <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center ring-2 ring-white">
            <Shield className="w-3 h-3 text-amber-400" />
          </div>
        </div>

        {/* Header & Explanatory Body */}
        <div className="space-y-2">
          <span className="inline-block text-[11px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
            Permission Boundary
          </span>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Access Restricted
          </h2>
          <p className="text-xs text-slate-600 leading-relaxed max-w-md mx-auto pt-1 font-sans">
            {customMessage || RESTRICTED_ACCESS_MESSAGE}
          </p>
        </div>

        {/* Neutral Information Box */}
        <div className="p-3.5 bg-slate-50/80 rounded-xl border border-slate-100 text-left space-y-1 text-slate-500">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
            Role Management Notice
          </span>
          <p className="text-[11px] leading-relaxed">
            Role-based access permissions are enforced in accordance with data governance policies. Use the demo role switcher in the top navigation bar to explore the application with another profile.
          </p>
        </div>

        {/* Navigation Action */}
        <div className="pt-1 flex items-center justify-center">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 transition-colors shadow-sm shadow-slate-900/10"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Overview Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AccessRestricted;
