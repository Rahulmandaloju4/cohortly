import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { RoleProvider } from './context/RoleContext';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LearnersPage } from './pages/LearnersPage';
import { CoursesPage } from './pages/CoursesPage';
import { CohortsPage } from './pages/CohortsPage';
import { ContentPage } from './pages/ContentPage';
import { ExceptionsPage } from './pages/ExceptionsPage';
import { GeneratorPage } from './pages/GeneratorPage';
import { AuditPage } from './pages/AuditPage';

export const App: React.FC = () => {
  return (
    <RoleProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="dashboard" element={<Navigate to="/" replace />} />
            <Route path="learners" element={<LearnersPage />} />
            <Route path="courses" element={<CoursesPage />} />
            <Route path="cohorts" element={<CohortsPage />} />
            <Route path="content" element={<ContentPage />} />
            <Route path="exceptions" element={<ExceptionsPage />} />
            <Route path="generator" element={<GeneratorPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </RoleProvider>
  );
};

export default App;
