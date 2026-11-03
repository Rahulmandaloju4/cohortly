import React, { useEffect, useState } from 'react';
import {
  Users,
  UserCheck,
  GraduationCap,
  BookOpen,
  TrendingUp,
  AlertTriangle,
  Activity,
  Layers,
  ArrowUpRight,
  ShieldAlert,
  Calendar,
  CheckCircle2,
  Clock,
  Sparkles,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  AreaChart,
} from 'recharts';
import { getDashboardOverview, getEngagementTrends, getCompletionTrends } from '../services/api';
import { useRole } from '../context/RoleContext';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const { role, roleInfo } = useRole();
  const [metrics, setMetrics] = useState<any>(null);
  const [engagementData, setEngagementData] = useState<any[]>([]);
  const [completionData, setCompletionData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, [role]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewRes, engRes, compRes] = await Promise.all([
        getDashboardOverview(),
        getEngagementTrends(6),
        getCompletionTrends(),
      ]);
      setMetrics(overviewRes);
      setEngagementData(engRes);
      setCompletionData(compRes);
    } catch (err: any) {
      console.error('Failed to load dashboard:', err);
      setError(err?.response?.data?.detail || 'Failed to load dashboard analytics from backend.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium text-slate-500">Computing platform metrics and cohort intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
        <div className="flex items-center space-x-3">
          <ShieldAlert className="w-6 h-6 text-rose-600 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold">Access Restriction / Error</h3>
            <p className="text-xs text-rose-600 mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchDashboardData}
          className="mt-4 px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-medium hover:bg-rose-700 transition-colors"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner / Intelligence Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200">
              Live Relational Telemetry
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 font-mono">Reference Anchor: Oct 22, 2026</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Executive Overview & Cohort Health
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Turn learning data into actionable intelligence across active cohorts, courses, and retention funnels.
          </p>
        </div>

        {/* Quick Deduplication Policy Stat */}
        <div className="flex items-center gap-3 bg-white px-4 py-2.5 rounded-xl border border-slate-200 shadow-sm text-xs">
          <Layers className="w-4 h-4 text-blue-600" />
          <div>
            <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Two-Tier Dedup</div>
            <div className="text-slate-700 font-medium">
              <span className="font-bold text-slate-900">{metrics?.deduplicated_events?.toLocaleString()}</span> valid / {metrics?.total_activity_events?.toLocaleString()} raw
            </div>
          </div>
        </div>
      </div>

      {/* 8 Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: WALER */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">WALER (Learner Engagement)</span>
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-blue-600">{metrics?.waler}%</span>
            <span className="text-xs text-emerald-600 font-medium flex items-center">
              Active / Eligible
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Distinct active learners in past 7 days vs registered eligible pool.
          </p>
        </div>

        {/* KPI 2: WAEER */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">WAEER (Enrollment Rate)</span>
            <span className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
              <Activity className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-indigo-600">{metrics?.waeer}%</span>
            <span className="text-xs text-slate-500 font-medium">Enrollment Window</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Distinct active course enrollments with interactions in 7-day window.
          </p>
        </div>

        {/* KPI 3: Completion Rate */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">Overall Completion Rate</span>
            <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
              <GraduationCap className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-emerald-600">
              {metrics?.overall_completion_rate}%
            </span>
            <span className="text-xs text-slate-500 font-medium">Across Cohorts</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Graduated students meeting active 80% content + 70% exam rules.
          </p>
        </div>

        {/* KPI 4: At-Risk Learners */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">At-Risk Learners</span>
            <span className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
              <AlertTriangle className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-amber-600">
              {metrics?.at_risk_learner_count}
            </span>
            <span className="text-xs text-amber-700 font-medium bg-amber-50 px-2 py-0.5 rounded">
              0 events &gt;14d
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Enrolled students with zero activity in last 14 days or failing tests.
          </p>
        </div>

        {/* KPI 5: Active Learners */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">Active Students</span>
            <span className="p-1.5 rounded-lg bg-slate-100 text-slate-600">
              <Users className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-800">
              {metrics?.active_learners}
            </span>
            <span className="text-xs text-slate-500">/ {metrics?.total_learners} Total</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Registered learners currently marked in active standing.
          </p>
        </div>

        {/* KPI 6: Active Courses */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">Curriculum Catalog</span>
            <span className="p-1.5 rounded-lg bg-slate-100 text-slate-600">
              <BookOpen className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-800">
              {metrics?.total_courses}
            </span>
            <span className="text-xs text-slate-500">Courses ({metrics?.active_cohorts} Cohorts)</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Active intermediate, beginner, and advanced AI curriculum.
          </p>
        </div>

        {/* KPI 7: Total Enrollments */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">Total Enrollments</span>
            <span className="p-1.5 rounded-lg bg-slate-100 text-slate-600">
              <UserCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-slate-800">
              {metrics?.total_enrollments}
            </span>
            <span className="text-xs text-slate-500">Seats</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Across North America, Europe, Asia Pacific, and Latin America.
          </p>
        </div>

        {/* KPI 8: Active Anomalies */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm card-hover-effect">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-600">Active Quality Anomalies</span>
            <span className="p-1.5 rounded-lg bg-rose-50 text-rose-600">
              <ShieldAlert className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-rose-600">
              {metrics?.active_anomaly_count}
            </span>
            <span className="text-xs text-rose-700 font-medium bg-rose-50 px-2 py-0.5 rounded">
              Triage Required
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 line-clamp-1">
            Detected relational violations, duplicates, or premature completions.
          </p>
        </div>
      </div>

      {/* Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Multi-Week Engagement Trend */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                Multi-Week Engagement Rates (WALER vs WAEER)
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Comparison of Learner Active Rate (WALER) vs Enrollment Active Rate (WAEER).
              </p>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={engagementData}>
                <defs>
                  <linearGradient id="colorWaler" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorWaeer" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis unit="%" tick={{ fontSize: 11, fill: '#64748B' }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  formatter={(val: any) => [`${val}%`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Area type="monotone" dataKey="waler" name="WALER (Learner Active %)" stroke="#2563EB" strokeWidth={2.5} fillOpacity={1} fill="url(#colorWaler)" />
                <Area type="monotone" dataKey="waeer" name="WAEER (Enrollment Active %)" stroke="#8B5CF6" strokeWidth={2} fillOpacity={1} fill="url(#colorWaeer)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Cohort Graduation Rate Comparison */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-emerald-600" />
                Cohort Graduation & Average Score Progression
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Cohort-level completion percentage and final assessment attainment.
              </p>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={completionData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="cohort_name" tick={{ fontSize: 10, fill: '#64748B' }} tickFormatter={(name) => name.split(' ')[1] || name} />
                <YAxis unit="%" tick={{ fontSize: 11, fill: '#64748B' }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  formatter={(val: any) => [`${val}%`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar dataKey="completion_rate" name="Completion Rate (%)" fill="#10B981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="avg_score" name="Avg Final Score" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Actionable Insights & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quality Anomalies Alert Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm lg:col-span-1">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              Active Quality Anomalies
            </h4>
            <Link
              to="/exceptions"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              Investigate <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="mt-4 space-y-3">
            {metrics?.active_anomalies_breakdown && metrics.active_anomalies_breakdown.length > 0 ? (
              metrics.active_anomalies_breakdown.map((item: any) => {
                const isCritical = item.severity === 'CRITICAL';
                const isHigh = item.severity === 'HIGH';
                const bgClass = isCritical ? 'bg-rose-50 border-rose-100' : isHigh ? 'bg-amber-50 border-amber-100' : 'bg-blue-50 border-blue-100';
                const dotClass = isCritical ? 'bg-rose-500 animate-ping' : isHigh ? 'bg-amber-500' : 'bg-blue-500';
                const textHeaderClass = isCritical ? 'text-rose-900' : isHigh ? 'text-amber-900' : 'text-blue-900';
                const textDescClass = isCritical ? 'text-rose-700' : isHigh ? 'text-amber-700' : 'text-blue-700';

                return (
                  <div key={item.issue_type} className={`p-3 rounded-lg border flex items-start space-x-3 ${bgClass}`}>
                    <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${dotClass}`}></span>
                    <div className="text-xs">
                      <div className="flex items-center gap-2">
                        <span className={`font-bold ${textHeaderClass}`}>{item.issue_type}</span>
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-white/80 border border-slate-200 text-slate-700">
                          {item.count} {item.count === 1 ? 'record' : 'records'}
                        </span>
                      </div>
                      <p className={`${textDescClass} mt-0.5`}>
                        {item.description}
                      </p>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-100 text-center text-xs text-emerald-800">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 mx-auto mb-1" />
                <span className="font-semibold">All Anomalies Resolved</span>
                <p className="text-emerald-600 text-[11px] mt-0.5">Platform relational integrity is currently 100% clean.</p>
              </div>
            )}
          </div>
        </div>

        {/* At-Risk Learner Summary */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm lg:col-span-2">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Learner Retention & Early Warning Signals
            </h4>
            <Link
              to="/learners"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View All Directory <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="text-xs font-semibold text-slate-800 flex items-center justify-between">
                <span>Inactivity Threshold</span>
                <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px] font-bold">
                  &gt; 14 Days Idle
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Learners with active enrollments who logged zero interactions in the last 14 days. Early automated intervention increases graduation retention by 34%.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
              <div className="text-xs font-semibold text-slate-800 flex items-center justify-between">
                <span>Assessment Deficiencies</span>
                <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 text-[10px] font-bold">
                  Score &lt; 70.0%
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Learners who failed midterm technical assessments and have remaining attempt allowances to resubmit prior to final outcome evaluation.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
