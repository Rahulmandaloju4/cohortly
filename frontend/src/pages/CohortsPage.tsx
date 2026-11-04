import React, { useEffect, useState } from 'react';
import {
  Users,
  Calendar,
  Globe,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  BarChart2,
  Search,
  Filter,
  X,
  ArrowRight,
  ShieldAlert,
  Layers,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import {
  getCohorts,
  getCohortAnalytics,
  compareCohorts,
} from '../services/api';
import { useRole } from '../context/RoleContext';
import { AccessRestricted } from '../components/AccessRestricted';
import { classifyApiError } from '../utils/errors';

const COHORT_COLORS = [
  '#2563EB', // blue
  '#10B981', // emerald
  '#8B5CF6', // purple
  '#F59E0B', // amber
  '#EC4899', // pink
  '#06B6D4', // cyan
];

export const CohortsPage: React.FC = () => {
  const { role } = useRole();
  const [cohorts, setCohorts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isRestricted, setIsRestricted] = useState<boolean>(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [programFilter, setProgramFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [regionFilter, setRegionFilter] = useState<string>('');

  // Single Cohort Detail Drawer
  const [selectedCohortId, setSelectedCohortId] = useState<string | null>(null);
  const [cohortAnalytics, setCohortAnalytics] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  // Multi-Cohort Comparison
  const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<any | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState<boolean>(false);
  const [showComparisonModal, setShowComparisonModal] = useState<boolean>(false);

  useEffect(() => {
    if (role === 'LEARNER') {
      setIsRestricted(true);
      setLoading(false);
      return;
    }
    setIsRestricted(false);
    fetchCohorts();
  }, [role]);

  const fetchCohorts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCohorts();
      setCohorts(data || []);
    } catch (err: any) {
      console.error('Failed to load cohorts', err);
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

  const handleSelectCohort = async (cohortId: string) => {
    setSelectedCohortId(cohortId);
    setDetailLoading(true);
    try {
      const data = await getCohortAnalytics(cohortId);
      setCohortAnalytics(data);
    } catch (err) {
      console.error('Failed to load cohort analytics', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const toggleComparisonSelection = (cohortId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedForComparison((prev) => {
      if (prev.includes(cohortId)) {
        return prev.filter((id) => id !== cohortId);
      } else {
        if (prev.length >= 6) {
          alert('You can compare up to 6 cohorts simultaneously.');
          return prev;
        }
        return [...prev, cohortId];
      }
    });
  };

  const handleRunComparison = async () => {
    if (selectedForComparison.length < 2) {
      alert('Please select at least 2 cohorts to compare.');
      return;
    }
    setComparisonLoading(true);
    setShowComparisonModal(true);
    try {
      const res = await compareCohorts(selectedForComparison);
      setComparisonData(res);
    } catch (err) {
      console.error('Failed to compare cohorts', err);
    } finally {
      setComparisonLoading(false);
    }
  };

  const filteredCohorts = cohorts.filter((c) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      if (!c.cohort_name.toLowerCase().includes(q) && !c.cohort_id.toLowerCase().includes(q)) {
        return false;
      }
    }
    if (programFilter && c.program_type !== programFilter) return false;
    if (statusFilter && c.status !== statusFilter) return false;
    if (regionFilter && c.region !== regionFilter) return false;
    return true;
  });

  const regions = Array.from(new Set(cohorts.map((c) => c.region))).filter(Boolean);
  const programTypes = Array.from(new Set(cohorts.map((c) => c.program_type))).filter(Boolean);

  // Transform comparison data for Recharts LineChart
  const chartDays = [0, 7, 14, 21, 28, 35, 42];
  const chartData = chartDays.map((day) => {
    const point: Record<string, any> = { day: `Day ${day}` };
    if (comparisonData?.cohorts) {
      comparisonData.cohorts.forEach((coh: any) => {
        const found = coh.engagement_timeline?.find((t: any) => t.day_number === day);
        point[coh.cohort_name] = found ? found.metric_value : 0;
      });
    }
    return point;
  });

  if (isRestricted) {
    return <AccessRestricted />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Cohort Intelligence & Comparison</h2>
          <p className="text-sm text-slate-500">
            Monitor cohort health trajectories, compare normalized retention timelines, and detect at-risk cohorts.
          </p>
        </div>

        {/* Multi-Cohort Compare Trigger Button */}
        <div className="flex items-center gap-3">
          {selectedForComparison.length > 0 && (
            <span className="text-xs text-slate-500 font-medium">
              {selectedForComparison.length} selected
            </span>
          )}
          <button
            onClick={handleRunComparison}
            disabled={selectedForComparison.length < 2}
            className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all shadow-sm ${
              selectedForComparison.length >= 2
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-500/20'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Compare Cohorts ({selectedForComparison.length})
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by cohort name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-semibold pl-1">
            <Filter className="w-3.5 h-3.5" />
            Filters:
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="CONCLUDED">Concluded</option>
            <option value="UPCOMING">Upcoming</option>
          </select>

          <select
            value={programFilter}
            onChange={(e) => setProgramFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Programs</option>
            {programTypes.map((pt) => (
              <option key={pt} value={pt}>
                {pt}
              </option>
            ))}
          </select>

          <select
            value={regionFilter}
            onChange={(e) => setRegionFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Regions</option>
            {regions.map((reg) => (
              <option key={reg} value={reg}>
                {reg}
              </option>
            ))}
          </select>

          {(searchQuery || statusFilter || programFilter || regionFilter) && (
            <button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('');
                setProgramFilter('');
                setRegionFilter('');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Cohorts Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading cohort intelligence...</div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>
      ) : filteredCohorts.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
          No cohorts found matching the filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCohorts.map((coh) => {
            const isSelected = selectedForComparison.includes(coh.cohort_id);

            return (
              <div
                key={coh.cohort_id}
                onClick={() => handleSelectCohort(coh.cohort_id)}
                className={`bg-white rounded-xl border p-5 shadow-sm hover:shadow-md transition-all cursor-pointer flex flex-col justify-between group ${
                  isSelected ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-slate-200'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {coh.program_type}
                    </span>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border ${
                          coh.status === 'ACTIVE'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : coh.status === 'CONCLUDED'
                            ? 'bg-slate-100 text-slate-600 border-slate-200'
                            : 'bg-blue-50 text-blue-700 border-blue-200'
                        }`}
                      >
                        {coh.status}
                      </span>

                      {/* Compare Checkbox */}
                      <button
                        onClick={(e) => toggleComparisonSelection(coh.cohort_id, e)}
                        title="Select for comparison"
                        className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                          isSelected
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : 'border-slate-300 hover:border-blue-400 bg-white'
                        }`}
                      >
                        {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1 mb-1">
                    {coh.cohort_name}
                  </h3>
                  <span className="text-xs text-slate-400 font-mono block mb-3">{coh.cohort_id}</span>

                  <div className="space-y-1.5 text-xs text-slate-600 mb-4">
                    <div className="flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5 text-slate-400" />
                      <span>{coh.region}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span className="font-mono text-[11px]">
                        {coh.start_date} to {coh.end_date}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-100 pt-3 mt-2">
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="bg-slate-50 p-2 rounded-lg">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Enrolled</span>
                      <span className="text-sm font-bold text-slate-800">{coh.total_enrollments}</span>
                    </div>
                    <div className="bg-slate-50 p-2 rounded-lg">
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Graduation Rate</span>
                      <span className="text-sm font-bold text-emerald-600">{coh.completion_rate}%</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-blue-600 font-semibold mt-3 group-hover:translate-x-0.5 transition-transform">
                    <span>Inspect Cohort Health</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Single Cohort Detail Drawer */}
      {selectedCohortId && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex justify-end">
          <div className="bg-white w-full max-w-xl h-full shadow-2xl overflow-y-auto flex flex-col animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    {cohortAnalytics?.cohort_name || 'Cohort Profile'}
                  </h3>
                  <span className="text-xs font-mono text-slate-400">{selectedCohortId}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedCohortId(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="p-6 space-y-6 flex-1">
              {detailLoading ? (
                <div className="p-12 text-center text-slate-400">Loading cohort metrics...</div>
              ) : cohortAnalytics ? (
                <>
                  {/* Meta Information */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Region</span>
                      <span className="font-semibold text-slate-800">{cohortAnalytics.region}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Program Type</span>
                      <span className="font-semibold text-slate-800">{cohortAnalytics.program_type}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Start Date</span>
                      <span className="font-mono text-slate-700">{cohortAnalytics.start_date}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">End Date</span>
                      <span className="font-mono text-slate-700">{cohortAnalytics.end_date}</span>
                    </div>
                  </div>

                  {/* Dual Engagement Rates: WALER vs WAEER */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        Active Engagement Metrics
                      </h4>
                      <span className="text-[11px] text-blue-600 font-medium">Denominator-Aligned</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200">
                        <span className="text-[10px] uppercase font-bold text-blue-700 block mb-1">
                          WALER (Learner Rate)
                        </span>
                        <div className="flex items-baseline gap-1">
                          <span className="text-2xl font-bold text-blue-900">{cohortAnalytics.waler}%</span>
                        </div>
                        <span className="text-[11px] text-blue-700/80 mt-1 block">
                          Distinct active learners ÷ eligible active learners.
                        </span>
                      </div>

                      <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200">
                        <span className="text-[10px] uppercase font-bold text-indigo-700 block mb-1">
                          WAEER (Enrollment Rate)
                        </span>
                        <div className="flex items-baseline gap-1">
                          <span className="text-2xl font-bold text-indigo-900">{cohortAnalytics.waeer}%</span>
                        </div>
                        <span className="text-[11px] text-indigo-700/80 mt-1 block">
                          Distinct active enrollments ÷ eligible active enrollments.
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Enrollment Status Breakdown */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Enrollment Funnel Status
                    </h4>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="p-3 rounded-lg bg-blue-50/50 border border-blue-100">
                        <span className="text-[10px] font-bold uppercase text-blue-600 block">Active</span>
                        <span className="text-lg font-bold text-blue-900">{cohortAnalytics.active_count}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-emerald-50/50 border border-emerald-100">
                        <span className="text-[10px] font-bold uppercase text-emerald-600 block">Completed</span>
                        <span className="text-lg font-bold text-emerald-900">{cohortAnalytics.completed_count}</span>
                      </div>
                      <div className="p-3 rounded-lg bg-rose-50/50 border border-rose-100">
                        <span className="text-[10px] font-bold uppercase text-rose-600 block">Dropped</span>
                        <span className="text-lg font-bold text-rose-900">{cohortAnalytics.dropped_count}</span>
                      </div>
                    </div>
                  </div>

                  {/* Learner Risk Distribution */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        Learner Risk Distribution
                      </h4>
                      <span className="text-[11px] font-mono text-slate-400">
                        {cohortAnalytics.risk_distribution?.HIGH || 0} High Risk
                      </span>
                    </div>

                    {/* Risk Bar */}
                    <div className="h-3 w-full bg-slate-100 rounded-full flex overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full"
                        style={{
                          width: `${
                            cohortAnalytics.active_count > 0
                              ? ((cohortAnalytics.risk_distribution?.LOW || 0) / cohortAnalytics.active_count) * 100
                              : 0
                          }%`,
                        }}
                        title={`Low Risk: ${cohortAnalytics.risk_distribution?.LOW || 0}`}
                      />
                      <div
                        className="bg-amber-500 h-full"
                        style={{
                          width: `${
                            cohortAnalytics.active_count > 0
                              ? ((cohortAnalytics.risk_distribution?.MEDIUM || 0) / cohortAnalytics.active_count) * 100
                              : 0
                          }%`,
                        }}
                        title={`Medium Risk: ${cohortAnalytics.risk_distribution?.MEDIUM || 0}`}
                      />
                      <div
                        className="bg-rose-500 h-full"
                        style={{
                          width: `${
                            cohortAnalytics.active_count > 0
                              ? ((cohortAnalytics.risk_distribution?.HIGH || 0) / cohortAnalytics.active_count) * 100
                              : 0
                          }%`,
                        }}
                        title={`High Risk: ${cohortAnalytics.risk_distribution?.HIGH || 0}`}
                      />
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-xs pt-1">
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                        <span>Low: {cohortAnalytics.risk_distribution?.LOW || 0}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                        <span>Med: {cohortAnalytics.risk_distribution?.MEDIUM || 0}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                        <span>High: {cohortAnalytics.risk_distribution?.HIGH || 0}</span>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl text-slate-500 text-xs">
                  Cohort analytics unavailable.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Multi-Cohort Comparison Modal */}
      {showComparisonModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-5xl max-h-[90vh] shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-blue-600" />
                <h3 className="text-lg font-bold text-slate-900">
                  Normalized Multi-Cohort Comparison
                </h3>
              </div>
              <button
                onClick={() => setShowComparisonModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {comparisonLoading ? (
                <div className="p-16 text-center text-slate-400">
                  Computing normalized multi-cohort timelines...
                </div>
              ) : comparisonData ? (
                <>
                  {/* Normalized Retention Timeline Chart */}
                  <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">
                          Normalized Engagement Timeline (% Active Retention)
                        </h4>
                        <p className="text-xs text-slate-500">
                          Trajectories aligned to Day 0 (Cohort Launch Date) over a 6-week window.
                        </p>
                      </div>
                    </div>

                    <div className="h-72 w-full pt-4">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="day" stroke="#94a3b8" fontSize={11} />
                          <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#0f172a',
                              borderColor: '#1e293b',
                              borderRadius: '8px',
                              color: '#fff',
                              fontSize: '12px',
                            }}
                          />
                          <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                          {comparisonData.cohorts?.map((coh: any, idx: number) => (
                            <Line
                              key={coh.cohort_id}
                              type="monotone"
                              dataKey={coh.cohort_name}
                              stroke={COHORT_COLORS[idx % COHORT_COLORS.length]}
                              strokeWidth={2.5}
                              dot={{ r: 4 }}
                              activeDot={{ r: 6 }}
                            />
                          ))}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Comparative Metrics Table */}
                  <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                    <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                        Cross-Cohort Benchmark Metrics
                      </h4>
                    </div>

                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50/50 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-200">
                        <tr>
                          <th className="py-2.5 px-4 font-semibold">Cohort</th>
                          <th className="py-2.5 px-4 font-semibold">Program</th>
                          <th className="py-2.5 px-4 font-semibold text-center">Enrollments</th>
                          <th className="py-2.5 px-4 font-semibold text-center">Day 0 WALER</th>
                          <th className="py-2.5 px-4 font-semibold text-center">Graduation Rate</th>
                          <th className="py-2.5 px-4 font-semibold text-center">Avg Final Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {comparisonData.cohorts?.map((coh: any, idx: number) => (
                          <tr key={coh.cohort_id} className="hover:bg-slate-50/50">
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <span
                                  className="w-3 h-3 rounded-full flex-shrink-0"
                                  style={{ backgroundColor: COHORT_COLORS[idx % COHORT_COLORS.length] }}
                                />
                                <span className="font-bold text-slate-800">{coh.cohort_name}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-600">{coh.program_type}</td>
                            <td className="py-3 px-4 font-mono font-semibold text-slate-800 text-center">
                              {coh.total_enrollments}
                            </td>
                            <td className="py-3 px-4 font-mono text-blue-600 font-bold text-center">
                              {coh.waler}%
                            </td>
                            <td className="py-3 px-4 font-mono text-emerald-600 font-bold text-center">
                              {coh.completion_rate}%
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-700 text-center">
                              {coh.average_score !== null ? `${coh.average_score}` : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-slate-400">No comparison data available.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
