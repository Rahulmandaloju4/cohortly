import React, { useEffect, useState } from 'react';
import {
  FileText,
  Video,
  HelpCircle,
  Code,
  FolderOpen,
  Filter,
  BarChart2,
  TrendingDown,
  Clock,
  Eye,
  AlertTriangle,
  Sparkles,
  BookOpen,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  Legend,
} from 'recharts';
import {
  getCourses,
  getContentUsageAnalytics,
  getCourseAnalytics,
} from '../services/api';

export const ContentPage: React.FC = () => {
  const [courses, setCourses] = useState<any[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>('');
  const [usageItems, setUsageItems] = useState<any[]>([]);
  const [courseAnalytics, setCourseAnalytics] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCourses();
  }, []);

  useEffect(() => {
    loadContentData();
  }, [selectedCourseId]);

  const loadCourses = async () => {
    try {
      const data = await getCourses({ page: 1, page_size: 100 });
      setCourses(data.items || []);
      if (data.items?.length > 0 && !selectedCourseId) {
        setSelectedCourseId(data.items[0].course_id);
      }
    } catch (err) {
      console.error('Failed to load courses for content selector', err);
    }
  };

  const loadContentData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [usageData, analyticsData] = await Promise.all([
        getContentUsageAnalytics(selectedCourseId || undefined),
        selectedCourseId ? getCourseAnalytics(selectedCourseId).catch(() => null) : Promise.resolve(null),
      ]);
      setUsageItems(usageData || []);
      setCourseAnalytics(analyticsData);
    } catch (err: any) {
      console.error('Failed to load content analytics', err);
      setError('Unable to load content analytics. Please verify backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'VIDEO':
        return <Video className="w-3.5 h-3.5 text-blue-500" />;
      case 'READING':
        return <FileText className="w-3.5 h-3.5 text-emerald-500" />;
      case 'QUIZ':
        return <HelpCircle className="w-3.5 h-3.5 text-purple-500" />;
      case 'ASSIGNMENT':
      case 'LAB':
        return <Code className="w-3.5 h-3.5 text-amber-500" />;
      default:
        return <FolderOpen className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  // Aggregated KPIs
  const totalViews = usageItems.reduce((acc, cur) => acc + (cur.views_count || 0), 0);
  const avgEstimated = usageItems.length > 0
    ? (usageItems.reduce((acc, cur) => acc + cur.estimated_duration_minutes, 0) / usageItems.length).toFixed(1)
    : '0';
  const avgActual = usageItems.length > 0
    ? (usageItems.reduce((acc, cur) => acc + cur.avg_session_duration_minutes, 0) / usageItems.length).toFixed(1)
    : '0';

  // Identify high-friction hotspot (highest drop-off rate)
  const sortedByDrop = [...usageItems].sort((a, b) => b.drop_off_pct - a.drop_off_pct);
  const highestDropItem = sortedByDrop[0] || null;

  // Chart data: sequence progression
  const chartData = usageItems.map((item) => ({
    name: `#${item.sequence_number} ${item.title.length > 18 ? item.title.slice(0, 18) + '...' : item.title}`,
    views: item.views_count,
    dropRate: item.drop_off_pct,
    estMins: item.estimated_duration_minutes,
    actMins: item.avg_session_duration_minutes,
  }));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Content & Drop-off Funnel</h2>
          <p className="text-sm text-slate-500">
            Curriculum sequence progression, drop-off hotspots, and estimated vs. actual engagement duration.
          </p>
        </div>

        {/* Course Selector Dropdown */}
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-slate-400" />
          <select
            value={selectedCourseId}
            onChange={(e) => setSelectedCourseId(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
          >
            <option value="">All Courses (Global)</option>
            {courses.map((crs) => (
              <option key={crs.course_id} value={crs.course_id}>
                {crs.course_name} ({crs.course_id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Analyzed Items</span>
            <FileText className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{usageItems.length}</div>
          <p className="text-[11px] text-slate-400">Content nodes in sequence</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Total Views Logged</span>
            <Eye className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalViews.toLocaleString()}</div>
          <p className="text-[11px] text-slate-400">Deduplicated interaction events</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Avg Session Duration</span>
            <Clock className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900">{avgActual}m</span>
            <span className="text-xs text-slate-400 font-mono">/ est {avgEstimated}m</span>
          </div>
          <p className="text-[11px] text-slate-400">Paced vs planned study duration</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold">
            <span>Top Drop-off Hotspot</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-rose-600">
              {highestDropItem ? `${highestDropItem.drop_off_pct}%` : '0%'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 line-clamp-1 font-mono">
            {highestDropItem ? `#${highestDropItem.sequence_number} ${highestDropItem.title}` : 'None detected'}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400">Loading content progression and drop-off analytics...</div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>
      ) : (
        <>
          {/* Funnel Waterfall Chart */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Sequence Drop-off Waterfall</h3>
                <p className="text-xs text-slate-500">
                  Learners reaching each successive content sequence item.
                </p>
              </div>
              <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2.5 py-1 rounded">
                {usageItems.length} Content Items
              </span>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="name"
                    stroke="#94a3b8"
                    fontSize={10}
                    interval={0}
                    angle={-25}
                    textAnchor="end"
                  />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '15px' }} />
                  <Bar dataKey="views" name="Interaction Views" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Content Items Detail Table: Estimated vs Actual Duration & Drop-off */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="px-5 py-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Detailed Lesson Performance & Friction Hotspots
              </h3>
              <span className="text-[11px] font-mono text-slate-400">
                Sorted by sequence order
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/50 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">Seq #</th>
                    <th className="py-2.5 px-4 font-semibold">Content Title</th>
                    <th className="py-2.5 px-4 font-semibold">Course</th>
                    <th className="py-2.5 px-4 font-semibold">Type</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Views</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Est. Duration</th>
                    <th className="py-2.5 px-4 font-semibold text-center">Avg Session</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Drop-off Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {usageItems.map((item) => {
                    const isHotspot = item.drop_off_pct >= 10.0;

                    return (
                      <tr
                        key={item.content_id}
                        className={`hover:bg-slate-50/50 ${isHotspot ? 'bg-rose-50/20' : ''}`}
                      >
                        <td className="py-3 px-4 font-mono font-bold text-slate-500">
                          #{item.sequence_number}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {getContentTypeIcon(item.content_type)}
                            <div>
                              <span className="font-bold text-slate-800">{item.title}</span>
                              <span className="text-[10px] font-mono text-slate-400 block">
                                {item.content_id}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-slate-600">{item.course_name}</td>
                        <td className="py-3 px-4">
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-slate-100 text-slate-600 uppercase">
                            {item.content_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono font-semibold text-slate-800 text-center">
                          {item.views_count.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-500 text-center">
                          {item.estimated_duration_minutes}m
                        </td>
                        <td className="py-3 px-4 font-mono font-bold text-slate-700 text-center">
                          {item.avg_session_duration_minutes}m
                        </td>
                        <td className="py-3 px-4 text-right">
                          <span
                            className={`inline-flex items-center gap-1 font-mono font-bold text-xs px-2 py-0.5 rounded ${
                              isHotspot
                                ? 'bg-rose-100 text-rose-700 border border-rose-200'
                                : 'text-slate-600 bg-slate-100'
                            }`}
                          >
                            {isHotspot && <TrendingDown className="w-3 h-3 text-rose-600" />}
                            {item.drop_off_pct}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
