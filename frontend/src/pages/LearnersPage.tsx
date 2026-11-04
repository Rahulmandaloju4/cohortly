import React, { useEffect, useState } from 'react';
import {
  Users,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  BookOpen,
  Calendar,
  Layers,
  X,
  FileText,
  Activity,
  Check,
  Award,
} from 'lucide-react';
import { getLearners, getLearnerDetail, getLearnerActivity } from '../services/api';
import { useRole } from '../context/RoleContext';
import { AccessRestricted } from '../components/AccessRestricted';
import { classifyApiError } from '../utils/errors';

export const LearnersPage: React.FC = () => {
  const { role } = useRole();
  const [learners, setLearners] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [regionFilter, setRegionFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRestricted, setIsRestricted] = useState(false);

  // Selected learner detail drawer
  const [selectedLearnerId, setSelectedLearnerId] = useState<string | null>(null);
  const [learnerDetail, setLearnerDetail] = useState<any | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'activity'>('profile');
  const [activityTimeline, setActivityTimeline] = useState<any[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (role === 'LEARNER') {
      setIsRestricted(true);
      setLoading(false);
      return;
    }
    setIsRestricted(false);
    fetchLearners();
  }, [page, search, statusFilter, regionFilter, role]);

  const fetchLearners = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLearners({
        page,
        page_size: pageSize,
        search: search || undefined,
        status: statusFilter || undefined,
        region: regionFilter || undefined,
      });
      setLearners(data.items);
      setTotal(data.total);
    } catch (err: any) {
      console.error('Failed to load learners:', err);
      const classified = classifyApiError(err);
      if (classified.isAccessRestricted) {
        setIsRestricted(true);
      } else {
        setError(classified.userMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectLearner = async (id: string) => {
    setSelectedLearnerId(id);
    setDetailLoading(true);
    setActiveTab('profile');
    try {
      const [detail, activity] = await Promise.all([
        getLearnerDetail(id),
        getLearnerActivity(id, { page_size: 20 }),
      ]);
      setLearnerDetail(detail);
      setActivityTimeline(activity.items);
    } catch (err) {
      console.error('Failed to load learner detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">HIGH RISK</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">MEDIUM RISK</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">ON TRACK</span>;
    }
  };

  if (isRestricted) {
    return <AccessRestricted />;
  }

  return (
    <div className="space-y-6">
      {/* Page Title & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-blue-600" />
            Learners Directory
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Student roster, enrollment progression, explainable graduation checklists, and activity timelines.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search name, email, or ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 w-56 text-slate-800 placeholder-slate-400"
            />
          </div>

          {/* Region */}
          <select
            value={regionFilter}
            onChange={(e) => {
              setRegionFilter(e.target.value);
              setPage(1);
            }}
            className="text-xs py-1.5 px-2.5 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">All Regions</option>
            <option value="North America">North America</option>
            <option value="Europe">Europe</option>
            <option value="Asia Pacific">Asia Pacific</option>
            <option value="Latin America">Latin America</option>
          </select>

          {/* Status */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="text-xs py-1.5 px-2.5 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="INACTIVE">INACTIVE</option>
            <option value="SUSPENDED">SUSPENDED</option>
          </select>
        </div>
      </div>

      {/* Learners Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Learner Profile</th>
                <th className="py-3 px-4">Region</th>
                <th className="py-3 px-4">Learning Mode</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Active Seats</th>
                <th className="py-3 px-4">Completed</th>
                <th className="py-3 px-4">Retention Risk</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                    Loading learners...
                  </td>
                </tr>
              ) : learners.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No learners match the specified search and filter criteria.
                  </td>
                </tr>
              ) : (
                learners.map((lrn) => (
                  <tr
                    key={lrn.learner_id}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                    onClick={() => handleSelectLearner(lrn.learner_id)}
                  >
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                        {lrn.full_name}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {lrn.email} • {lrn.learner_id}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-600">{lrn.region}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
                        {lrn.learning_mode}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="flex items-center gap-1.5 font-medium text-emerald-700">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        {lrn.learner_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-slate-800">
                      {lrn.active_enrollment_count}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-slate-800">
                      {lrn.completed_enrollment_count}
                    </td>
                    <td className="py-3 px-4">{getRiskBadge(lrn.overall_risk_level)}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectLearner(lrn.learner_id);
                        }}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
                      >
                        Inspect <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing <span className="font-semibold text-slate-800">{learners.length}</span> of{' '}
            <span className="font-semibold text-slate-800">{total}</span> learners
          </span>
          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-2.5 py-1 rounded border border-slate-200 bg-white text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 flex items-center gap-1"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Previous
            </button>
            <span className="px-2 font-mono">
              {page} / {totalPages || 1}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="px-2.5 py-1 rounded border border-slate-200 bg-white text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 flex items-center gap-1"
            >
              Next <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide-over Inspection Drawer */}
      {selectedLearnerId && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-sm flex justify-end animate-in fade-in duration-150">
          <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col z-50">
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-200 flex items-start justify-between bg-slate-50">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs text-slate-400">{learnerDetail?.learner_id}</span>
                  {learnerDetail && getRiskBadge(learnerDetail.overall_risk_level)}
                </div>
                <h3 className="text-xl font-bold text-slate-900 mt-1">
                  {learnerDetail?.full_name || 'Loading...'}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5 font-mono">
                  {learnerDetail?.email} • Registered {learnerDetail?.registration_date} • {learnerDetail?.region}
                </p>
              </div>
              <button
                onClick={() => setSelectedLearnerId(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Tabs */}
            <div className="flex border-b border-slate-200 px-6 bg-white text-xs font-semibold">
              <button
                onClick={() => setActiveTab('profile')}
                className={`py-3 px-4 border-b-2 flex items-center gap-2 transition-colors ${
                  activeTab === 'profile'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <BookOpen className="w-4 h-4" /> Enrollments & Explainable Outcomes
              </button>
              <button
                onClick={() => setActiveTab('activity')}
                className={`py-3 px-4 border-b-2 flex items-center gap-2 transition-colors ${
                  activeTab === 'activity'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Activity className="w-4 h-4" /> Activity Stream Audit Log
              </button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {detailLoading ? (
                <div className="py-20 text-center text-slate-400">
                  <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  Loading comprehensive telemetry...
                </div>
              ) : activeTab === 'profile' ? (
                <>
                  {/* Risk Warning Box */}
                  {learnerDetail?.risk_factors?.length > 0 && (
                    <div className="p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 text-xs">
                      <div className="font-bold flex items-center gap-1.5 text-amber-800">
                        <AlertTriangle className="w-4 h-4 text-amber-600" /> Early Warning Retention Factors
                      </div>
                      <ul className="list-disc pl-5 mt-2 space-y-1 text-amber-800">
                        {learnerDetail.risk_factors.map((rf: string, idx: number) => (
                          <li key={idx}>{rf}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Course Enrollments & Transparent Outcome Checklists */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Enrolled Courses ({learnerDetail?.enrollments?.length || 0})
                    </h4>

                    {learnerDetail?.enrollments?.map((enr: any) => (
                      <div
                        key={enr.enrollment_id}
                        className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                              {enr.cohort_name}
                            </span>
                            <h5 className="text-base font-bold text-slate-900">{enr.course_name}</h5>
                            <span className="text-xs text-slate-400 font-mono">
                              Enrolled: {enr.enrolled_at.slice(0, 10)} • ID: {enr.enrollment_id}
                            </span>
                          </div>
                          <span
                            className={`text-xs px-2.5 py-1 rounded-full font-bold uppercase border ${
                              enr.enrollment_status === 'COMPLETED'
                                ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                                : enr.enrollment_status === 'DROPPED'
                                ? 'bg-rose-100 text-rose-800 border-rose-200'
                                : 'bg-blue-100 text-blue-800 border-blue-200'
                            }`}
                          >
                            {enr.enrollment_status}
                          </span>
                        </div>

                        {/* Progress Indicators */}
                        <div className="grid grid-cols-2 gap-4 pt-2">
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Content Completion</span>
                              <span className="font-bold text-slate-800">
                                {enr.content_completion_percentage}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-100 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${Math.min(100, enr.content_completion_percentage)}%` }}
                              />
                            </div>
                          </div>

                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Final Assessment Score</span>
                              <span className="font-bold text-slate-800">
                                {enr.final_assessment_score !== null ? `${enr.final_assessment_score}/100` : 'Not attempted'}
                              </span>
                            </div>
                            <div className="w-full bg-slate-100 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full transition-all ${
                                  (enr.final_assessment_score || 0) >= 70 ? 'bg-emerald-500' : 'bg-amber-500'
                                }`}
                                style={{ width: `${Math.min(100, enr.final_assessment_score || 0)}%` }}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Explainable Completion Decision Checklist */}
                        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
                          <div className="flex items-center justify-between text-slate-700 font-semibold">
                            <span className="flex items-center gap-1.5">
                              <Award className="w-4 h-4 text-indigo-600" />
                              Outcome Engine Snapshot (v{enr.outcome_version || 1})
                            </span>
                            <span className="text-[11px] font-mono text-slate-500">
                              Status: {enr.outcome_status || 'PENDING'}
                            </span>
                          </div>

                          <div className="text-[11px] text-slate-600 font-mono bg-white p-2.5 rounded border border-slate-200/80">
                            {enr.explainable_outcome?.explanation ||
                              enr.explainable_outcome?.reason ||
                              'Outcome evaluation active according to governing completion rule.'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                /* Granular Activity Stream Timeline */
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-xs text-slate-500 pb-2 border-b border-slate-200">
                    <span>Recent Activity Stream ({activityTimeline.length} events)</span>
                    <span className="text-[11px] font-mono">Deduplicated Stream</span>
                  </div>

                  <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                    {activityTimeline.length === 0 ? (
                      <p className="text-xs text-slate-400">No events logged yet.</p>
                    ) : (
                      activityTimeline.map((evt) => (
                        <div key={evt.event_id} className="relative text-xs">
                          <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-blue-600 border-2 border-white ring-1 ring-blue-500" />
                          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                            <div className="flex items-center justify-between text-slate-800 font-semibold">
                              <span className="font-mono text-blue-700">{evt.event_type}</span>
                              <span className="text-[10px] text-slate-400 font-mono">
                                {evt.event_timestamp_utc.slice(0, 19).replace('T', ' ')} UTC
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-500 mt-1 flex flex-wrap gap-x-3 gap-y-1">
                              <span>Local Date: <strong className="text-slate-700 font-mono">{evt.local_event_date}</strong></span>
                              <span>Timezone: <strong className="text-slate-700">{evt.source_timezone}</strong></span>
                              <span>Device: <strong className="text-slate-700">{evt.device_type}</strong></span>
                              <span>Sync: <strong className="text-slate-700">{evt.sync_status}</strong></span>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
