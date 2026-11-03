import React, { createContext, useContext, useState, useEffect } from 'react';

export type DemoRole = 'PLATFORM_ADMIN' | 'ACADEMIC_ADMIN' | 'INSTRUCTOR' | 'SUPPORT_STAFF' | 'LEARNER';

export interface RoleInfo {
  id: DemoRole;
  title: string;
  badge: string;
  description: string;
  color: string;
}

export const ROLE_DEFINITIONS: Record<DemoRole, RoleInfo> = {
  PLATFORM_ADMIN: {
    id: 'PLATFORM_ADMIN',
    title: 'Platform Administrator',
    badge: 'Superuser',
    description: 'Full unconstrained system authority: synthetic data generator, manifest checksums, and DB management.',
    color: 'bg-purple-100 text-purple-800 border-purple-200',
  },
  ACADEMIC_ADMIN: {
    id: 'ACADEMIC_ADMIN',
    title: 'Academic Administrator',
    badge: 'Admin',
    description: 'Institution-wide oversight: cohort health, curriculum benchmarks, and 15-point validation audits.',
    color: 'bg-blue-100 text-blue-800 border-blue-200',
  },
  INSTRUCTOR: {
    id: 'INSTRUCTOR',
    title: 'Course Instructor',
    badge: 'Faculty',
    description: 'Curriculum delivery: drop-off funnel analytics, student progress, and assessment attempt scoring.',
    color: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  },
  SUPPORT_STAFF: {
    id: 'SUPPORT_STAFF',
    title: 'Student Support Specialist',
    badge: 'Support',
    description: 'Operational investigator: anomaly detection triage, activity timelines, and state history audits.',
    color: 'bg-amber-100 text-amber-800 border-amber-200',
  },
  LEARNER: {
    id: 'LEARNER',
    title: 'Active Student',
    badge: 'Student',
    description: 'Course participant: personal syllabus, transparent graduation checklist, and self-progress view.',
    color: 'bg-slate-100 text-slate-800 border-slate-200',
  },
};

interface RoleContextType {
  role: DemoRole;
  roleInfo: RoleInfo;
  setRole: (role: DemoRole) => void;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

export const RoleProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRoleState] = useState<DemoRole>(() => {
    const saved = localStorage.getItem('cohortly_demo_role');
    return (saved as DemoRole) || 'PLATFORM_ADMIN';
  });

  const setRole = (newRole: DemoRole) => {
    setRoleState(newRole);
    localStorage.setItem('cohortly_demo_role', newRole);
  };

  useEffect(() => {
    localStorage.setItem('cohortly_demo_role', role);
  }, [role]);

  return (
    <RoleContext.Provider value={{ role, roleInfo: ROLE_DEFINITIONS[role], setRole }}>
      {children}
    </RoleContext.Provider>
  );
};

export const useRole = (): RoleContextType => {
  const ctx = useContext(RoleContext);
  if (!ctx) {
    throw new Error('useRole must be used within a RoleProvider');
  }
  return ctx;
};
