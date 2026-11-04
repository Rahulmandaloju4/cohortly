import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Play,
  RefreshCw,
  Hash,
  Scale,
  Award,
  Sparkles,
  Layers,
  ArrowRight,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  getDataValidation,
  getDataBenchmark,
  getDataManifest,
} from '../services/api';
import { useRole } from '../context/RoleContext';
import { AccessRestricted } from '../components/AccessRestricted';
import { classifyApiError } from '../utils/errors';

export const AuditPage: React.FC = () => {
  const { role } = useRole();
  const [validationReport, setValidationReport] = useState<any | null>(null);
  const [benchmarkScorecard, setBenchmarkScorecard] = useState<any | null>(null);
  const [manifestData, setManifestData] = useState<any | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isRestricted, setIsRestricted] = useState<boolean>(false);

  const [runningAudit, setRunningAudit] = useState<boolean>(false);
  const [runningBenchmark, setRunningBenchmark] = useState<boolean>(false);
  const [showManifest, setShowManifest] = useState<boolean>(false);

  useEffect(() => {
    fetchAllAuditData();
  }, [role]);

  const fetchAllAuditData = async () => {
    // Audit page is restricted to PLATFORM_ADMIN and ACADEMIC_ADMIN
    if (role !== 'PLATFORM_ADMIN' && role !== 'ACADEMIC_ADMIN') {
      setIsRestricted(true);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setIsRestricted(false);

      // Resilient sequential loading to prevent SQLite concurrency lockups
      let valRes = null;
      try {
        valRes = await getDataValidation();
      } catch (valErr: any) {
        const classified = classifyApiError(valErr);
        if (classified.isAccessRestricted) {
          setIsRestricted(true);
          return;
        }
        setError(classified.userMessage);
        return;
      }
      setValidationReport(valRes);

      // Next load benchmark scorecard
      const benchRes = await getDataBenchmark().catch((benchErr: any) => {
        const classified = classifyApiError(benchErr);
        if (classified.isAccessRestricted) setIsRestricted(true);
        return null;
      });
      setBenchmarkScorecard(benchRes);

      // Finally load table manifest
      const manRes = await getDataManifest().catch((manErr: any) => {
        const classified = classifyApiError(manErr);
        if (classified.isAccessRestricted) setIsRestricted(true);
        return null;
      });
      setManifestData(manRes);
    } catch (err: any) {
      console.error('Failed to load validation audit data', err);
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

  const handleRunAudit = async () => {
    setRunningAudit(true);
    try {
      const data = await getDataValidation(true);
      setValidationReport(data);
    } catch (err: any) {
      console.error('Audit execution error', err);
      const classified = classifyApiError(err);
      if (classified.isAccessRestricted) {
        setIsRestricted(true);
      } else {
        setError(classified.userMessage);
      }
    } finally {
      setRunningAudit(false);
    }
  };

  const handleRunBenchmark = async () => {
    setRunningBenchmark(true);
    try {
      const data = await getDataBenchmark();
      setBenchmarkScorecard(data);
    } catch (err: any) {
      console.error('Benchmark execution error', err);
      const classified = classifyApiError(err);
      if (classified.isAccessRestricted) {
        setIsRestricted(true);
      } else {
        setError(classified.userMessage);
      }
    } finally {
      setRunningBenchmark(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASSED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'WARNING':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'FAILED':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
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
            Quality Audit & Decoupled Benchmark
          </h2>
          <p className="text-sm text-slate-500">
            15-Point Cross-Entity Integrity Suite, decoupled ground-truth evaluation, and SHA-256 table manifests.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunBenchmark}
            disabled={runningBenchmark}
            className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-indigo-500/20 disabled:opacity-50"
          >
            <Scale className={`w-3.5 h-3.5 ${runningBenchmark ? 'animate-spin' : ''}`} />
            Run Benchmark Scorecard
          </button>

          <button
            onClick={handleRunAudit}
            disabled={runningAudit}
            className="px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm shadow-blue-500/20 disabled:opacity-50"
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${runningAudit ? 'animate-spin' : ''}`} />
            Re-run 15-Point Audit
          </button>
        </div>
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400">Loading comprehensive quality audit...</div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>
      ) : (
        <>
          {/* SECTION 1: DECOUPLED BENCHMARK SCORECARD */}
          {benchmarkScorecard?.aggregate && (
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-indigo-600" />
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Decoupled Evaluation Benchmark Scorecard
                    </h3>
                    <p className="text-xs text-slate-500">
                      Ground truth isolated in <code className="font-mono text-slate-700">data/ground_truth/anomalies.json</code> vs operational detection ledger
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono bg-indigo-50 text-indigo-700 px-3 py-1 rounded-lg border border-indigo-200 font-bold">
                    Zero Operational Leakage
                  </span>
                </div>
              </div>

              {/* 4 Scorecard KPI Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Precision
                  </span>
                  <span className="text-2xl font-bold text-emerald-600 font-mono">
                    {(benchmarkScorecard.aggregate.precision * 100).toFixed(1)}%
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-1">
                    TP / (TP + FP)
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Recall
                  </span>
                  <span className="text-2xl font-bold text-blue-600 font-mono">
                    {(benchmarkScorecard.aggregate.recall * 100).toFixed(1)}%
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-1">
                    TP / (TP + FN)
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    F1 Score
                  </span>
                  <span className="text-2xl font-bold text-purple-600 font-mono">
                    {(benchmarkScorecard.aggregate.f1_score * 100).toFixed(1)}%
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-1">
                    Harmonic mean
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                    Detections
                  </span>
                  <span className="text-2xl font-bold text-slate-800 font-mono">
                    {benchmarkScorecard.aggregate.true_positives} / {benchmarkScorecard.total_ground_truth}
                  </span>
                  <span className="text-[10px] text-slate-500 block mt-1">
                    True Positives vs Total GT
                  </span>
                </div>
              </div>

              {/* By-Anomaly-Type Breakdown Table */}
              {benchmarkScorecard.by_anomaly_type && (
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                      Performance Breakdown by Anomaly Category
                    </span>
                  </div>

                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/50 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-200">
                      <tr>
                        <th className="py-2 px-4 font-semibold">Anomaly Category</th>
                        <th className="py-2 px-4 font-semibold text-center">Ground Truth</th>
                        <th className="py-2 px-4 font-semibold text-center">Detected</th>
                        <th className="py-2 px-4 font-semibold text-center">TP / FP / FN</th>
                        <th className="py-2 px-4 font-semibold text-center">Precision</th>
                        <th className="py-2 px-4 font-semibold text-center">Recall</th>
                        <th className="py-2 px-4 font-semibold text-right">F1 Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.entries(benchmarkScorecard.by_anomaly_type).map(([itype, m]: [string, any]) => (
                        <tr key={itype} className="hover:bg-slate-50/50">
                          <td className="py-2.5 px-4 font-mono font-bold text-slate-800">
                            {itype}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-center text-slate-600">
                            {m.ground_truth_count}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-center text-slate-600">
                            {m.detected_count}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-center text-slate-700">
                            <span className="text-emerald-600 font-bold">{m.true_positives}</span> /{' '}
                            <span className="text-amber-600">{m.false_positives}</span> /{' '}
                            <span className="text-rose-600">{m.false_negatives}</span>
                          </td>
                          <td className="py-2.5 px-4 font-mono text-emerald-600 font-bold text-center">
                            {(m.precision * 100).toFixed(1)}%
                          </td>
                          <td className="py-2.5 px-4 font-mono text-blue-600 font-bold text-center">
                            {(m.recall * 100).toFixed(1)}%
                          </td>
                          <td className="py-2.5 px-4 font-mono text-purple-600 font-bold text-right">
                            {(m.f1_score * 100).toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* SECTION 2: 15-POINT INTEGRITY VALIDATION AUDIT */}
          {validationReport && (
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-blue-600" />
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      15-Point Cross-Entity Relational & Lifecycle Validation Suite
                    </h3>
                    <p className="text-xs text-slate-500">
                      Full relational consistency audit covering referential integrity, chronology, and rule alignment
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold">
                    {validationReport.passed_checks} / {validationReport.total_checks} PASSED
                  </span>
                  {validationReport.warning_checks > 0 && (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-200 font-bold">
                      {validationReport.warning_checks} Tracked Anomalies
                    </span>
                  )}
                </div>
              </div>

              {/* 15 Checks Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {validationReport.checks?.map((chk: any) => (
                  <div
                    key={chk.check_id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col justify-between space-y-2 hover:bg-slate-50 transition-colors"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-1.5">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                          {chk.check_id} • {chk.category}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${getStatusBadge(
                            chk.status
                          )}`}
                        >
                          {chk.status}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-900">{chk.name}</h4>
                    </div>

                    <p className="text-[11px] text-slate-600 leading-relaxed pt-1 border-t border-slate-200/60 font-sans">
                      {chk.details}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION 3: SHA-256 REPRODUCIBILITY TABLE MANIFEST */}
          {manifestData?.tables && (
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div
                onClick={() => setShowManifest(!showManifest)}
                className="flex items-center justify-between cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  <Hash className="w-5 h-5 text-emerald-600" />
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Deterministic SHA-256 Table Manifest & Checksums
                    </h3>
                    <p className="text-xs text-slate-500">
                      Bit-for-bit verification of all 13 relational tables generated with seed {manifestData.seed}
                    </p>
                  </div>
                </div>

                <button className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 font-semibold">
                  <span>{showManifest ? 'Hide Manifest' : 'View Checksums'}</span>
                  {showManifest ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>

              {showManifest && (
                <div className="border border-slate-200 rounded-xl overflow-hidden pt-2">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-200">
                      <tr>
                        <th className="py-2 px-4 font-semibold">Table</th>
                        <th className="py-2 px-4 font-semibold text-center">Row Count</th>
                        <th className="py-2 px-4 font-semibold font-mono">SHA-256 Checksum Hash</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {manifestData.tables.map((t: any) => (
                        <tr key={t.table_name} className="hover:bg-slate-50/50">
                          <td className="py-2.5 px-4 font-mono font-bold text-slate-800">
                            {t.table_name}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-center text-slate-600">
                            {t.row_count.toLocaleString()}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-[11px] text-slate-500 truncate select-all">
                            {t.sha256_checksum}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};
