import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Layers,
  Award,
  Clock,
  User,
  CheckCircle2,
  BarChart2,
  ChevronRight,
  ChevronDown,
  Search,
  Filter,
  GraduationCap,
  X,
  FileText,
  Video,
  HelpCircle,
  Code,
  FolderOpen,
  ArrowRight,
  Percent,
} from 'lucide-react';
import {
  getCourses,
  getCourseDetail,
  getCourseAnalytics,
} from '../services/api';

export const CoursesPage: React.FC = () => {
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Selected Course for Detail Drawer
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null);
  const [courseDetail, setCourseDetail] = useState<any | null>(null);
  const [courseAnalytics, setCourseAnalytics] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [expandedModules, setExpandedModules] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState<'curriculum' | 'rules' | 'funnel'>('curriculum');

  useEffect(() => {
    fetchCourses();
  }, [categoryFilter, difficultyFilter, statusFilter]);

  const fetchCourses = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: Record<string, any> = { page: 1, page_size: 50 };
      if (categoryFilter) params.category = categoryFilter;
      if (difficultyFilter) params.difficulty = difficultyFilter;
      if (statusFilter) params.status = statusFilter;

      const data = await getCourses(params);
      setCourses(data.items || []);
    } catch (err: any) {
      console.error('Failed to load courses', err);
      setError('Unable to load course catalog. Please ensure the backend is active.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCourse = async (courseId: string) => {
    setSelectedCourseId(courseId);
    setDetailLoading(true);
    try {
      const [detailData, analyticsData] = await Promise.all([
        getCourseDetail(courseId),
        getCourseAnalytics(courseId).catch(() => null), // Gracefully handle if role lacks analytics access
      ]);
      setCourseDetail(detailData);
      setCourseAnalytics(analyticsData);

      // Auto-expand all modules by default
      const initialExpanded: Record<string, boolean> = {};
      detailData?.curriculum?.forEach((mod: any) => {
        initialExpanded[mod.content_id] = true;
      });
      setExpandedModules(initialExpanded);
    } catch (err) {
      console.error('Failed to fetch course details', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const toggleModule = (moduleId: string) => {
    setExpandedModules((prev) => ({
      ...prev,
      [moduleId]: !prev[moduleId],
    }));
  };

  const filteredCourses = courses.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.course_name.toLowerCase().includes(q) ||
      c.course_id.toLowerCase().includes(q) ||
      c.instructor_name.toLowerCase().includes(q) ||
      c.category.toLowerCase().includes(q)
    );
  });

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

  const categories = Array.from(new Set(courses.map((c) => c.category))).filter(Boolean);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Courses & Curriculum</h2>
          <p className="text-sm text-slate-500">
            Interactive curriculum explorer, active completion rules, and lesson drop-off funnel analytics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono bg-blue-50 text-blue-700 px-3 py-1.5 rounded-lg border border-blue-200">
            {courses.length} Courses in Catalog
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by course name, ID, or instructor..."
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
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Difficulties</option>
            <option value="BEGINNER">Beginner</option>
            <option value="INTERMEDIATE">Intermediate</option>
            <option value="ADVANCED">Advanced</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="ARCHIVED">Archived</option>
          </select>

          {(categoryFilter || difficultyFilter || statusFilter || searchQuery) && (
            <button
              onClick={() => {
                setCategoryFilter('');
                setDifficultyFilter('');
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

      {/* Course Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading course catalog...</div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">{error}</div>
      ) : filteredCourses.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
          No courses found matching the search criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCourses.map((crs) => (
            <div
              key={crs.course_id}
              onClick={() => handleSelectCourse(crs.course_id)}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-blue-400 transition-all cursor-pointer flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                    {crs.category}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border ${
                      crs.difficulty_level === 'BEGINNER'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : crs.difficulty_level === 'INTERMEDIATE'
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'bg-purple-50 text-purple-700 border-purple-200'
                    }`}
                  >
                    {crs.difficulty_level}
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1 mb-1">
                  {crs.course_name}
                </h3>
                <span className="text-xs text-slate-400 font-mono block mb-3">{crs.course_id}</span>

                <div className="flex items-center gap-1.5 text-xs text-slate-600 mb-4">
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  <span>{crs.instructor_name}</span>
                </div>
              </div>

              <div className="border-t border-slate-100 pt-3 mt-2">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Enrolled</span>
                    <span className="text-sm font-bold text-slate-800">{crs.total_enrollments}</span>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Grad. Rate</span>
                    <span className="text-sm font-bold text-emerald-600">{crs.completion_rate}%</span>
                  </div>
                  <div className="bg-slate-50 p-2 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Avg Score</span>
                    <span className="text-sm font-bold text-blue-600">
                      {crs.avg_assessment_score !== null ? `${crs.avg_assessment_score}` : '—'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-blue-600 font-semibold mt-3 group-hover:translate-x-0.5 transition-transform">
                  <span>Inspect Curriculum & Rules</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Slide-over Course Inspection Drawer */}
      {selectedCourseId && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex justify-end">
          <div className="bg-white w-full max-w-2xl h-full shadow-2xl overflow-y-auto flex flex-col animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-blue-600" />
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{courseDetail?.course_name || 'Course Profile'}</h3>
                  <span className="text-xs font-mono text-slate-400">{selectedCourseId}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedCourseId(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-slate-200 px-6 bg-slate-50 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('curriculum')}
                className={`py-3 px-3 border-b-2 flex items-center gap-1.5 ${
                  activeTab === 'curriculum'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Layers className="w-4 h-4" />
                Curriculum Tree
              </button>
              <button
                onClick={() => setActiveTab('rules')}
                className={`py-3 px-3 border-b-2 flex items-center gap-1.5 ${
                  activeTab === 'rules'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Award className="w-4 h-4" />
                Active Completion Rule
              </button>
              <button
                onClick={() => setActiveTab('funnel')}
                className={`py-3 px-3 border-b-2 flex items-center gap-1.5 ${
                  activeTab === 'funnel'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <BarChart2 className="w-4 h-4" />
                Drop-off Funnel
              </button>
            </div>

            {/* Drawer Body */}
            <div className="p-6 space-y-6 flex-1">
              {detailLoading ? (
                <div className="p-12 text-center text-slate-400">Loading course curriculum and rules...</div>
              ) : (
                <>
                  {/* Instructor & Metadata Banner */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block">Instructor</span>
                      <span className="text-sm font-bold text-slate-800">{courseDetail?.instructor_name}</span>
                      <span className="text-xs text-slate-500 block">
                        {courseDetail?.department} • {courseDetail?.instructor_email}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs px-2.5 py-1 rounded bg-white border border-slate-200 font-mono text-slate-700 font-semibold">
                        {courseDetail?.category}
                      </span>
                      <span className="text-xs px-2.5 py-1 rounded bg-blue-50 border border-blue-200 font-bold text-blue-700">
                        {courseDetail?.difficulty_level}
                      </span>
                    </div>
                  </div>

                  {/* TAB 1: CURRICULUM TREE */}
                  {activeTab === 'curriculum' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between text-xs text-slate-500 pb-2 border-b border-slate-200">
                        <span>Curriculum Structure ({courseDetail?.curriculum?.length || 0} Modules)</span>
                        <span className="text-[11px] font-mono text-slate-400">Click module to expand</span>
                      </div>

                      <div className="space-y-3">
                        {courseDetail?.curriculum?.map((mod: any) => {
                          const isExpanded = expandedModules[mod.content_id];
                          const totalDuration = (mod.children || []).reduce(
                            (acc: number, c: any) => acc + (c.estimated_duration_minutes || 0),
                            0
                          );

                          return (
                            <div
                              key={mod.content_id}
                              className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm"
                            >
                              {/* Module Header */}
                              <div
                                onClick={() => toggleModule(mod.content_id)}
                                className="p-4 bg-slate-50/70 hover:bg-slate-100/70 transition-colors flex items-center justify-between cursor-pointer border-b border-slate-100"
                              >
                                <div className="flex items-center gap-3">
                                  {isExpanded ? (
                                    <ChevronDown className="w-4 h-4 text-slate-500" />
                                  ) : (
                                    <ChevronRight className="w-4 h-4 text-slate-500" />
                                  )}
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs font-mono font-bold text-blue-600">
                                        Mod {mod.sequence_number}
                                      </span>
                                      <h4 className="text-sm font-bold text-slate-900">{mod.title}</h4>
                                    </div>
                                    <span className="text-[11px] text-slate-400 font-mono">
                                      {mod.content_id} • {mod.children?.length || 0} lessons
                                    </span>
                                  </div>
                                </div>

                                <div className="flex items-center gap-3 text-xs text-slate-500">
                                  <div className="flex items-center gap-1 font-mono">
                                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                                    <span>{totalDuration} mins</span>
                                  </div>
                                </div>
                              </div>

                              {/* Nested Children Lessons */}
                              {isExpanded && (
                                <div className="divide-y divide-slate-100 pl-6 pr-4 py-1 bg-white">
                                  {mod.children?.map((lesson: any) => (
                                    <div
                                      key={lesson.content_id}
                                      className="py-2.5 flex items-center justify-between text-xs hover:bg-slate-50/50 px-2 rounded-lg transition-colors"
                                    >
                                      <div className="flex items-center gap-3">
                                        {getContentTypeIcon(lesson.content_type)}
                                        <div>
                                          <div className="flex items-center gap-2">
                                            <span className="font-mono text-slate-400 text-[11px]">
                                              {mod.sequence_number}.{lesson.sequence_number}
                                            </span>
                                            <span className="font-semibold text-slate-800">{lesson.title}</span>
                                          </div>
                                          <span className="text-[10px] text-slate-400 font-mono">
                                            {lesson.content_id}
                                          </span>
                                        </div>
                                      </div>

                                      <div className="flex items-center gap-2">
                                        <span className="text-[10px] font-mono text-slate-400">
                                          {lesson.estimated_duration_minutes} min
                                        </span>
                                        {lesson.is_required ? (
                                          <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-amber-50 text-amber-700 border border-amber-200">
                                            Required
                                          </span>
                                        ) : (
                                          <span className="text-[10px] px-2 py-0.5 rounded text-slate-400 border border-slate-200">
                                            Optional
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* TAB 2: ACTIVE COMPLETION RULE */}
                  {activeTab === 'rules' && (
                    <div className="space-y-4">
                      {courseDetail?.active_rule ? (
                        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
                          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                            <div className="flex items-center gap-2">
                              <Award className="w-5 h-5 text-indigo-600" />
                              <h4 className="text-base font-bold text-slate-900">
                                Governing Completion Rule
                              </h4>
                            </div>
                            <span className="text-xs font-mono px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-bold">
                              v{courseDetail.active_rule.rule_version}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                                Content Threshold
                              </span>
                              <div className="flex items-baseline gap-1">
                                <span className="text-2xl font-bold text-slate-900">
                                  {courseDetail.active_rule.minimum_content_completion_percentage}%
                                </span>
                              </div>
                              <span className="text-[11px] text-slate-500">
                                Minimum required content consumption before graduation.
                              </span>
                            </div>

                            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
                              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                                Assessment Passing Grade
                              </span>
                              <div className="flex items-baseline gap-1">
                                <span className="text-2xl font-bold text-slate-900">
                                  {courseDetail.active_rule.minimum_assessment_score}
                                </span>
                                <span className="text-xs text-slate-400">/ 100</span>
                              </div>
                              <span className="text-[11px] text-slate-500">
                                Minimum cumulative assessment score required.
                              </span>
                            </div>
                          </div>

                          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="text-slate-600 font-medium">Require All Mandatory Assessments:</span>
                              <span
                                className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                                  courseDetail.active_rule.require_all_mandatory_assessments
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : 'bg-slate-100 text-slate-600'
                                }`}
                              >
                                {courseDetail.active_rule.require_all_mandatory_assessments ? 'YES' : 'NO'}
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-600 font-medium">Rule ID:</span>
                              <span className="font-mono text-slate-500">{courseDetail.active_rule.rule_id}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-slate-600 font-medium">Effective Date:</span>
                              <span className="font-mono text-slate-500">
                                {courseDetail.active_rule.effective_from.slice(0, 10)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="p-6 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs">
                          No active completion rule assigned to this course.
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB 3: DROP-OFF FUNNEL ANALYTICS */}
                  {activeTab === 'funnel' && (
                    <div className="space-y-4">
                      {courseAnalytics ? (
                        <>
                          {/* Funnel KPI Cards */}
                          <div className="grid grid-cols-4 gap-3 text-center">
                            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Enrolled</span>
                              <span className="text-lg font-bold text-slate-900">
                                {courseAnalytics.total_enrolled}
                              </span>
                            </div>
                            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Active</span>
                              <span className="text-lg font-bold text-blue-600">
                                {courseAnalytics.active_count}
                              </span>
                            </div>
                            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Completed</span>
                              <span className="text-lg font-bold text-emerald-600">
                                {courseAnalytics.completed_count}
                              </span>
                            </div>
                            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                              <span className="text-[10px] uppercase font-bold text-slate-400 block">Dropped</span>
                              <span className="text-lg font-bold text-rose-600">
                                {courseAnalytics.dropped_count}
                              </span>
                            </div>
                          </div>

                          {/* Lesson-by-lesson Funnel List */}
                          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
                            <h5 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                              Content Retention Waterfall
                            </h5>

                            <div className="space-y-2">
                              {courseAnalytics.drop_off_funnel?.map((item: any, idx: number) => {
                                const reachPercent = courseAnalytics.total_enrolled > 0
                                  ? Math.round((item.learners_reached / courseAnalytics.total_enrolled) * 100)
                                  : 0;

                                return (
                                  <div
                                    key={item.content_id}
                                    className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 space-y-1.5"
                                  >
                                    <div className="flex items-center justify-between text-xs">
                                      <div className="flex items-center gap-2">
                                        <span className="font-mono font-bold text-slate-400 text-[11px]">
                                          #{item.sequence_number}
                                        </span>
                                        <span className="font-semibold text-slate-800 line-clamp-1">
                                          {item.title}
                                        </span>
                                      </div>
                                      <div className="flex items-center gap-3">
                                        <span className="font-mono text-slate-600">
                                          {item.learners_reached} reached ({reachPercent}%)
                                        </span>
                                        {item.drop_off_rate_percent > 0 && (
                                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                                            -{item.drop_off_rate_percent}% drop
                                          </span>
                                        )}
                                      </div>
                                    </div>

                                    {/* Retention Bar */}
                                    <div className="w-full bg-slate-200 rounded-full h-1.5">
                                      <div
                                        className="bg-blue-600 h-1.5 rounded-full"
                                        style={{ width: `${reachPercent}%` }}
                                      />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl text-slate-500 text-xs">
                          Analytics unavailable or restricted for your active role.
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
