import React, { useEffect, useState } from 'react';
import {
  Database,
  HardDrive,
  Play,
  Download,
  RefreshCw,
  FileSpreadsheet,
  Layers,
  Settings2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  FileJson,
} from 'lucide-react';
import {
  getDataStatus,
  triggerDataGeneration,
  getExportUrl,
} from '../services/api';
import { useRole } from '../context/RoleContext';
import { AccessRestricted } from '../components/AccessRestricted';
import { classifyApiError } from '../utils/errors';

const ALL_TABLES = [
  'instructors',
  'learners',
  'courses',
  'cohorts',
  'enrollments',
  'content_items',
  'activity_events',
  'assessments',
  'attempts',
  'completion_rules',
  'course_outcomes',
  'exceptions',
  'state_history',
];

export const GeneratorPage: React.FC = () => {
  const { role } = useRole();
  const [dataStatus, setDataStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isRestricted, setIsRestricted] = useState<boolean>(false);

  // Generator Configuration State
  const [profile, setProfile] = useState<'starter' | 'full' | 'custom'>('starter');
  const [seed, setSeed] = useState<number>(20261022);
  const [numLearners, setNumLearners] = useState<number>(200);
  const [numCourses, setNumCourses] = useState<number>(20);
  const [numEnrollments, setNumEnrollments] = useState<number>(500);
  const [numEvents, setNumEvents] = useState<number>(10000);

  // Execution State
  const [generating, setGenerating] = useState<boolean>(false);
  const [generationResult, setGenerationResult] = useState<string | null>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // Export State
  const [exportTable, setExportTable] = useState<string>('learners');
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');

  useEffect(() => {
    if (role !== 'PLATFORM_ADMIN' && role !== 'ACADEMIC_ADMIN') {
      setIsRestricted(true);
      setLoading(false);
      return;
    }
    setIsRestricted(false);
    fetchStatus();
  }, [role]);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDataStatus();
      setDataStatus(data);
    } catch (err: any) {
      console.error('Failed to load database status', err);
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

  const handleProfileChange = (p: 'starter' | 'full' | 'custom') => {
    setProfile(p);
    if (p === 'starter') {
      setNumLearners(200);
      setNumCourses(20);
      setNumEnrollments(500);
      setNumEvents(10000);
    } else if (p === 'full') {
      setNumLearners(10000);
      setNumCourses(100);
      setNumEnrollments(25000);
      setNumEvents(2000000);
    }
  };

  const handleRunGenerator = async (e: React.FormEvent) => {
    e.preventDefault();
    if (role !== 'PLATFORM_ADMIN') {
      alert('Access restricted: Only Platform Administrator can trigger synthetic data generation.');
      return;
    }
    setGenerating(true);
    setGenerationResult(null);
    setGenerationError(null);

    try {
      const payload: any = {
        profile,
        seed: Number(seed),
      };
      if (profile === 'custom') {
        payload.num_learners = Number(numLearners);
        payload.num_courses = Number(numCourses);
        payload.num_enrollments = Number(numEnrollments);
        payload.num_events = Number(numEvents);
      }

      const res = await triggerDataGeneration(payload);
      setGenerationResult(res.message);
      // Refresh status after generation
      await fetchStatus();
    } catch (err: any) {
      console.error('Data generation failed', err);
      setGenerationError(err.response?.data?.detail || err.message || 'Generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    const url = getExportUrl(exportFormat, exportTable);
    window.open(url, '_blank');
  };

  if (isRestricted) {
    return <AccessRestricted />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Synthetic Data Generator & Storage
          </h2>
          <p className="text-sm text-slate-500">
            Deterministic synthetic generator with fixed seed anchors, profile scaling, and RFC-compliant data exports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 text-xs font-semibold hover:bg-slate-50 flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Storage Status
          </button>
        </div>
      </div>

      {/* Database Health Overview Cards */}
      {dataStatus && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
              <span>Database File</span>
              <HardDrive className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {dataStatus.database_size_mb} MB
            </div>
            <p className="text-[11px] text-slate-400 font-mono truncate" title={dataStatus.database_file}>
              {dataStatus.database_file}
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
              <span>Total Records</span>
              <Database className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-2xl font-bold text-emerald-600">
              {dataStatus.total_records?.toLocaleString()}
            </div>
            <p className="text-[11px] text-slate-400">Across 13 relational tables</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
              <span>Active Scale Profile</span>
              <Layers className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl font-bold text-indigo-600 uppercase">
              {dataStatus.active_profile}
            </div>
            <p className="text-[11px] text-slate-400">
              {dataStatus.active_profile === 'starter' ? 'Quick validation profile' : 'Full benchmark profile'}
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
              <span>Last Generated</span>
              <Clock className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-sm font-bold text-slate-800 font-mono truncate">
              {dataStatus.last_generated_at ? dataStatus.last_generated_at.slice(0, 19).replace('T', ' ') : 'N/A'}
            </div>
            <p className="text-[11px] text-slate-400">Reference: 2026-10-22 00:00:00Z</p>
          </div>
        </div>
      )}

      {/* Main Generator & Export Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Generator Form (7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2">
              <Settings2 className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="text-base font-bold text-slate-900">Deterministic Generator Engine</h3>
                <p className="text-xs text-slate-500">Configure scale, seed parameter, and entity volumes</p>
              </div>
            </div>
            <span className="text-xs font-mono bg-blue-50 text-blue-700 px-2.5 py-1 rounded border border-blue-200">
              Seed: {seed}
            </span>
          </div>

          {generationResult && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block font-bold">Generation Successful!</strong>
                <span>{generationResult}</span>
              </div>
            </div>
          )}

          {generationError && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block font-bold">Generation Failed:</strong>
                <span>{generationError}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleRunGenerator} className="space-y-5">
            {/* Profile Selection */}
            <div>
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2">
                1. Select Generator Profile
              </label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => handleProfileChange('starter')}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    profile === 'starter'
                      ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <span className="text-xs font-bold text-slate-900 block">Starter Scale</span>
                  <span className="text-[11px] text-slate-500 block">200 LRN • 10k EVT</span>
                  <span className="text-[10px] text-emerald-600 font-semibold block mt-1">~3-5 seconds</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleProfileChange('full')}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    profile === 'full'
                      ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <span className="text-xs font-bold text-slate-900 block">Full Benchmark</span>
                  <span className="text-[11px] text-slate-500 block">10k LRN • 2M EVT</span>
                  <span className="text-[10px] text-amber-600 font-semibold block mt-1">~90-120 seconds</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleProfileChange('custom')}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    profile === 'custom'
                      ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <span className="text-xs font-bold text-slate-900 block">Custom Presets</span>
                  <span className="text-[11px] text-slate-500 block">Manual Configuration</span>
                  <span className="text-[10px] text-blue-600 font-semibold block mt-1">Flexible limits</span>
                </button>
              </div>
            </div>

            {/* Seed Configuration */}
            <div>
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1">
                2. PRNG Deterministic Seed
              </label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full text-xs font-mono px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="20261022"
                required
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Standard anchor: <strong className="font-mono">20261022</strong> ensures 100% reproducible entity IDs, timestamps, and anomalies.
              </span>
            </div>

            {/* Entity Volume Inputs (Active if custom) */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">Learners</label>
                <input
                  type="number"
                  disabled={profile !== 'custom'}
                  value={numLearners}
                  onChange={(e) => setNumLearners(Number(e.target.value))}
                  className="w-full text-xs font-mono px-3 py-1.5 border border-slate-200 rounded-lg disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">Courses</label>
                <input
                  type="number"
                  disabled={profile !== 'custom'}
                  value={numCourses}
                  onChange={(e) => setNumCourses(Number(e.target.value))}
                  className="w-full text-xs font-mono px-3 py-1.5 border border-slate-200 rounded-lg disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">Enrollments</label>
                <input
                  type="number"
                  disabled={profile !== 'custom'}
                  value={numEnrollments}
                  onChange={(e) => setNumEnrollments(Number(e.target.value))}
                  className="w-full text-xs font-mono px-3 py-1.5 border border-slate-200 rounded-lg disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">Activity Events</label>
                <input
                  type="number"
                  disabled={profile !== 'custom'}
                  value={numEvents}
                  onChange={(e) => setNumEvents(Number(e.target.value))}
                  className="w-full text-xs font-mono px-3 py-1.5 border border-slate-200 rounded-lg disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>
            </div>

            {/* Trigger Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={generating || role !== 'PLATFORM_ADMIN'}
                title={role !== 'PLATFORM_ADMIN' ? 'Generation triggers restricted to Platform Administrator' : undefined}
                className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  role === 'PLATFORM_ADMIN'
                    ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20 disabled:opacity-50'
                    : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                }`}
              >
                {generating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Synthesizing Relational Database ({profile})...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    <span>
                      {role === 'PLATFORM_ADMIN'
                        ? 'Generate Deterministic Dataset'
                        : 'Generate Dataset (Platform Admin Only)'}
                    </span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: One-Click Table Data Exporter (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 border-b border-slate-100 pb-4 mb-4">
              <Download className="w-5 h-5 text-emerald-600" />
              <div>
                <h3 className="text-base font-bold text-slate-900">Streaming Data Exporter</h3>
                <p className="text-xs text-slate-500">Download operational tables as RFC 4180 CSV or JSON</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Select Relational Table:
                </label>
                <select
                  value={exportTable}
                  onChange={(e) => setExportTable(e.target.value)}
                  className="w-full text-xs font-mono px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-semibold"
                >
                  {ALL_TABLES.map((tbl) => (
                    <option key={tbl} value={tbl}>
                      {tbl}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Export File Format:
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setExportFormat('csv')}
                    className={`p-3 rounded-xl border flex items-center gap-2 text-xs font-bold transition-all ${
                      exportFormat === 'csv'
                        ? 'border-emerald-600 bg-emerald-50/50 text-emerald-900 ring-2 ring-emerald-500/20'
                        : 'border-slate-200 text-slate-600'
                    }`}
                  >
                    <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                    <span>RFC 4180 CSV</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setExportFormat('json')}
                    className={`p-3 rounded-xl border flex items-center gap-2 text-xs font-bold transition-all ${
                      exportFormat === 'json'
                        ? 'border-emerald-600 bg-emerald-50/50 text-emerald-900 ring-2 ring-emerald-500/20'
                        : 'border-slate-200 text-slate-600'
                    }`}
                  >
                    <FileJson className="w-4 h-4 text-emerald-600" />
                    <span>Formatted JSON</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <button
              onClick={handleDownload}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center gap-2 shadow-md shadow-emerald-500/20 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Download {exportTable.toUpperCase()}.{exportFormat.toUpperCase()}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Relational Tables Storage Ledger */}
      {dataStatus?.tables && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Operational Database Table Ledger (13 Tables)
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              SQLite WAL Mode • Strict Foreign Keys
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/50 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Table Name</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Row Count</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Estimated Footprint</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Direct Export</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {dataStatus.tables.map((tbl: any) => (
                  <tr key={tbl.table_name} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-4 font-mono font-bold text-slate-800">
                      {tbl.table_name}
                    </td>
                    <td className="py-2.5 px-4 font-mono font-semibold text-slate-700 text-center">
                      {tbl.row_count.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-slate-500 text-center">
                      {tbl.size_estimate_kb} KB
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <a
                          href={getExportUrl('csv', tbl.table_name)}
                          className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-mono text-[10px] font-bold"
                          download
                        >
                          CSV
                        </a>
                        <a
                          href={getExportUrl('json', tbl.table_name)}
                          className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-mono text-[10px] font-bold"
                          download
                        >
                          JSON
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
