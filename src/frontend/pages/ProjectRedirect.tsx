import type { ReactElement } from "react";
import { Navigate, useParams } from "react-router-dom";
import { useProjectState } from "../hooks/useProjectState";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";

export function ProjectRedirect(): ReactElement {
  const { id = "" } = useParams();
  const { data, isLoading, isError, refetch } = useProjectState(id);
  if (isLoading) return <LoadingState />;
  if (isError || !data)
    return (
      <ErrorState
        message="无法加载项目"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  const phase =
    (data.project as { latest_reached_phase?: number })?.latest_reached_phase ??
    data.project?.current_phase ??
    0;
  return <Navigate to={`/projects/${id}/phases/${phase}`} replace />;
}
