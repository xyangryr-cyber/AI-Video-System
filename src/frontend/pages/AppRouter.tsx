import type { ReactElement } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ProjectList } from "./ProjectList";
import { NewProject } from "./NewProject";
import { WorkflowPage } from "./WorkflowPage";
import { ProjectRedirect } from "./ProjectRedirect";
import { SettingsPage } from "./SettingsPage";

export function AppRouter(): ReactElement {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#f8fafc]">
        <Routes>
          <Route path="/" element={<Navigate to="/projects" replace />} />
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/projects/new" element={<NewProject />} />
          <Route path="/projects/:id" element={<ProjectRedirect />} />
          <Route path="/projects/:id/phases/:phase" element={<WorkflowPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<div>404</div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
