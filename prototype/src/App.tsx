import React, { useState } from 'react';
import ProjectList from './pages/ProjectList';
import NewProject from './pages/NewProject';
import ProjectWorkflow from './pages/ProjectWorkflow';
import Settings from './pages/Settings';

export type RouteType = 'list' | 'new' | 'workflow' | 'settings';

export default function App() {
  const [currentRoute, setCurrentRoute] = useState<RouteType>('list');
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  const navigate = (route: RouteType, projectId?: string) => {
    setCurrentRoute(route);
    if (projectId) setActiveProjectId(projectId);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-[#1e293b] font-sans">
      {currentRoute === 'list' && <ProjectList onNavigate={navigate} />}
      {currentRoute === 'new' && <NewProject onNavigate={navigate} />}
      {currentRoute === 'workflow' && (
        <ProjectWorkflow
          projectId={activeProjectId}
          onNavigate={navigate}
        />
      )}
      {currentRoute === 'settings' && <Settings onNavigate={navigate} />}
    </div>
  );
}
