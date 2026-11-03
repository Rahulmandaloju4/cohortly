import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  Search,
  Eye,
  X,
  Send,
  FileCode,
  ShieldCheck,
  HelpCircle,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import {
  getExceptions,
  getExceptionDetail,
  updateExceptionStatus,
} from '../services/api';

export const ExceptionsPage: React.FC = () => {
  const [exceptions, setExceptions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Inspection & Triage Modal
  const [selectedExceptionId, setSelectedExceptionId] = useState<string | null>(null);
  const [exceptionDetail, setExceptionDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  // Triage Action State
  const [triageStatus, setTriageStatus] = useState<string>('INVESTIGATING');
  const [triageReason, setTriageReason] = useState<string>('');
  const [triageSubmitting, setTriageSubmitting] = useState<boolean>(false);
  const [triageMessage, setTriageMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchExceptions();
  }, [severityFilter, statusFilter]);

  const fetchExceptions = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: Record<string, any> = { page: 1, page_size: 100 };
      if (severityFilter) params.severity = severityFilter;
      if (statusFilter) params.resolution_status = statusFilter;

      const data = await getExceptions(params);
      setExceptions(data.items || []);
    } catch (err: any) {
      console.error('Failed to load exceptions', err);
      setError('Unable to load exceptions. Check role permissions or backend status.');
    } finally {
      setLoading(false);
    }
  };

  const handleInspect = async (exceptionId: string) => {
    setSelectedExceptionId(exceptionId);
    setDetailLoading(true);
    setTriageMessage(null);
    try {
      const data = await getExceptionDetail(exceptionId);
      setExceptionDetail(data);
      setTriageStatus(data.resolution_status === 'OPEN' ? 'INVESTIGATING' : data.resolution_status);
      setTriageReason('');
    } catch (err) {
      console.error('Failed to load exception detail', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleTriageSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedExceptionId) return;

    if (!triageReason.trim()) {
      alert('Please provide a reason for this status change to record in the audit trail.');
      return;
    }

    try {
      setTriageSubmitting(true);
      const res = await updateExceptionStatus(selectedExceptionId, {
        status: triageStatus,
        reason: triageReason,
        actor_id: 'DEMO-SUPPORT-AGENT',
      });
      setTriageMessage(res.message);
      // Refresh list and detail
      fetchExceptions();
      const updated = await getExceptionDetail(selectedExceptionId);
      setExceptionDetail(updated);
    } catch (err: any) {
      console.error('Failed to update exception status', err);
      alert('Error updating status: ' + (err.response?.data?.detail || err.message));
    } finally {
      setTriageSubmitting(false);
    }
  };

  const filteredExceptions = exceptions.filter((exc) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      exc.exception_id.toLowerCase().includes(q) ||
      exc.entity_id.toLowerCase().includes(q) ||
      exc.issue_type.toLowerCase().includes(q) ||
      exc.description.toLowerCase().includes(q)
    );
  });

  // KPI Calculations
  const totalCount = exceptions.length;
  const openCount = exceptions.filter((e) => e.resolution_status === 'OPEN').length;
  const criticalCount = exceptions.filter((e) => e.severity === 'CRITICAL').length;
  const resolvedCount = exceptions.filter(
    (e) => e.resolution_status === 'RESOLVED' || e.resolution_status === 'FALSE_POSITIVE'
  ).length;

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'MEDIUM':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getStatusBadge = (st: string) => {
    switch (st) {
      case 'OPEN':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'INVESTIGATING':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'RESOLVED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'FALSE_POSITIVE':
        return 'bg-slate-100 text-slate-600 border-slate-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Exceptions & Data Quality Investigator
          </h2>
          <p className="text-sm text-slate-500">
            Relational anomaly investigation, forensic JSON evidence payloads, and immutable state audit transitions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono bg-purple-50 text-purple-700 px-3 py-1.5 rounded-lg border border-purple-200 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Append-Only Audit History
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Total Anomalies</span>
            <AlertTriangle className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalCount}</div>
          <p className="text-[11px] text-slate-400">Captured in exception ledger</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Open & Untriaged</span>
            <Clock className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold text-rose-600">{openCount}</div>
          <p className="text-[11px] text-slate-400">Pending engineer investigation</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Critical Severity</span>
            <ShieldAlert className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600">{criticalCount}</div>
          <p className="text-[11px] text-slate-400">Direct integrity violations</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Resolved / Triaged</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-600">{resolvedCount}</div>
          <p className="text-[11px] text-slate-400">Audited with recorded transition</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by ID, entity, issue type, or description..."
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
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
            <option value="FALSE_POSITIVE">False Positive</option>
          </select>

          {(severityFilter || statusFilter || searchQuery) && (
            <button
              onClick={() => {
                setSeverityFilter('');
                setStatusFilter('');
                setSearchQuery('');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Exceptions Table */}
      {loading ? (
        <div className="p-16 text-center text-slate-400">Loading detected exceptions...</div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>
      ) : filteredExceptions.length === 0 ? (
        <div className="p-16 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
          No exceptions found matching criteria.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Operational Anomaly Ledger ({filteredExceptions.length} records)
            </h3>
            <span className="text-[11px] font-mono text-slate-400">
              Pure Relational Anomaly Detection
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/50 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Exception ID</th>
                  <th className="py-2.5 px-4 font-semibold">Severity</th>
                  <th className="py-2.5 px-4 font-semibold">Issue Type</th>
                  <th className="py-2.5 px-4 font-semibold">Entity</th>
                  <th className="py-2.5 px-4 font-semibold">Entity ID</th>
                  <th className="py-2.5 px-4 font-semibold">Detected At</th>
                  <th className="py-2.5 px-4 font-semibold text-center">Status</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredExceptions.map((exc) => (
                  <tr
                    key={exc.exception_id}
                    onClick={() => handleInspect(exc.exception_id)}
                    className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-slate-900 group-hover:text-blue-600">
                      {exc.exception_id}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border ${getSeverityBadge(
                          exc.severity
                        )}`}
                      >
                        {exc.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-800">
                      {exc.issue_type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                      {exc.entity_type}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-700">
                      {exc.entity_id}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                      {exc.detected_at.slice(0, 19).replace('T', ' ')}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${getStatusBadge(
                          exc.resolution_status
                        )}`}
                      >
                        {exc.resolution_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleInspect(exc.exception_id);
                        }}
                        className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-semibold px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Forensic Inspection & Status Triage Drawer */}
      {selectedExceptionId && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex justify-end">
          <div className="bg-white w-full max-w-2xl h-full shadow-2xl overflow-y-auto flex flex-col animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-600" />
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    Forensic Anomaly Inspection
                  </h3>
                  <span className="text-xs font-mono text-slate-400">{selectedExceptionId}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedExceptionId(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="p-6 space-y-6 flex-1">
              {detailLoading ? (
                <div className="p-16 text-center text-slate-400">Loading forensic evidence...</div>
              ) : exceptionDetail ? (
                <>
                  {/* Status Banner */}
                  <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-200">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">
                        Issue Type
                      </span>
                      <span className="text-base font-bold text-slate-900">
                        {exceptionDetail.issue_type.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-slate-500 block mt-0.5">
                        Target: <strong className="font-mono text-slate-700">{exceptionDetail.entity_type}</strong> ({exceptionDetail.entity_id})
                      </span>
                    </div>

                    <div className="flex flex-col items-end gap-1.5">
                      <span
                        className={`text-xs font-bold px-2.5 py-1 rounded-full uppercase border ${getSeverityBadge(
                          exceptionDetail.severity
                        )}`}
                      >
                        {exceptionDetail.severity}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${getStatusBadge(
                          exceptionDetail.resolution_status
                        )}`}
                      >
                        {exceptionDetail.resolution_status}
                      </span>
                    </div>
                  </div>

                  {/* Description Box */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Anomaly Summary
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {exceptionDetail.description}
                    </p>
                  </div>

                  {/* Relevant Rule & Remediation Plan */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100 space-y-1">
                      <span className="text-[10px] font-bold uppercase text-indigo-700 block">
                        Violated Business Rule
                      </span>
                      <p className="text-xs text-indigo-900 font-semibold font-mono">
                        {exceptionDetail.relevant_rule || 'N/A'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-100 space-y-1">
                      <span className="text-[10px] font-bold uppercase text-emerald-700 block">
                        Recommended Action
                      </span>
                      <p className="text-xs text-emerald-900 font-semibold">
                        {exceptionDetail.recommended_action || 'Inspect anomaly evidence.'}
                      </p>
                    </div>
                  </div>

                  {/* Forensic Evidence JSON Payload */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                      <span className="flex items-center gap-1.5">
                        <FileCode className="w-4 h-4 text-blue-600" />
                        Forensic Evidence Dictionary
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">JSON Payload</span>
                    </div>

                    <div className="bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs overflow-x-auto border border-slate-800 shadow-inner max-h-60">
                      <pre>
                        {typeof exceptionDetail.evidence === 'string'
                          ? exceptionDetail.evidence
                          : JSON.stringify(exceptionDetail.evidence, null, 2)}
                      </pre>
                    </div>
                  </div>

                  {/* Interactive Status Triage Form (Append-Only Audit) */}
                  <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-purple-600" />
                        Triage Resolution & Append Audit Log
                      </h4>
                      <span className="text-[11px] font-mono text-slate-400">
                        Immutable state_history
                      </span>
                    </div>

                    {triageMessage && (
                      <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs">
                        {triageMessage}
                      </div>
                    )}

                    <form onSubmit={handleTriageSubmit} className="space-y-4">
                      <div>
                        <label className="text-xs font-semibold text-slate-700 block mb-1">
                          Transition Resolution Status:
                        </label>
                        <select
                          value={triageStatus}
                          onChange={(e) => setTriageStatus(e.target.value)}
                          className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                        >
                          <option value="OPEN">OPEN (Unresolved)</option>
                          <option value="INVESTIGATING">INVESTIGATING (Under Review)</option>
                          <option value="RESOLVED">RESOLVED (Remediation Complete)</option>
                          <option value="FALSE_POSITIVE">FALSE POSITIVE (Dismissed)</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-slate-700 block mb-1">
                          Audit Trail Reason / Notes (Required):
                        </label>
                        <textarea
                          rows={3}
                          value={triageReason}
                          onChange={(e) => setTriageReason(e.target.value)}
                          placeholder="Document the technical rationale, verification steps, or remediation action taken..."
                          className="w-full text-xs p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans"
                        />
                      </div>

                      <div className="flex items-center justify-end gap-3 pt-1">
                        <button
                          type="button"
                          onClick={() => setSelectedExceptionId(null)}
                          className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={triageSubmitting || !triageReason.trim()}
                          className="px-4 py-2 rounded-lg text-xs font-bold bg-blue-600 text-white hover:bg-blue-700 flex items-center gap-1.5 shadow-sm disabled:opacity-50"
                        >
                          <Send className="w-3.5 h-3.5" />
                          {triageSubmitting ? 'Recording Audit...' : 'Commit Status Transition'}
                        </button>
                      </div>
                    </form>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-slate-400">Exception detail not found.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
