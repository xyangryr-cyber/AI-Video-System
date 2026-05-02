import { useState } from "react";
import type { ReactElement } from "react";
import type { ShotBinding } from "@frontend/types/shot_material_binding";
import { MaterialDetailDrawer } from "./MaterialDetailDrawer";

interface MaterialEntry {
  material_id: string;
  material_type: string;
  verification_status: "pending" | "verified" | "rejected" | "missing";
  shot_id: string;
}

interface Props {
  shots: ShotBinding[];
  materials: MaterialEntry[];
  anchorTexts: Record<string, string>;
  onRequestRefetch: (materialId: string) => void;
  onRequestChange: (chartId: string) => void;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-200",
  verified: "bg-green-200",
  rejected: "bg-orange-200",
  missing: "bg-red-200",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "待验证",
  verified: "已验证",
  rejected: "未通过",
  missing: "缺失",
};

export function Phase7AMatrix({
  shots,
  materials,
  anchorTexts,
  onRequestRefetch,
  onRequestChange,
}: Props): ReactElement {
  const [selectedMaterial, setSelectedMaterial] = useState<MaterialEntry | null>(null);

  const materialMap = new Map<string, MaterialEntry>();
  for (const m of materials) {
    materialMap.set(m.material_id, m);
  }

  const allMaterialIds = materials.map((m) => m.material_id);

  return (
    <div>
      <div role="grid" data-testid="phase7a-matrix" className="overflow-x-auto">
        <div role="row" className="flex border-b font-medium text-xs">
          <div role="columnheader" className="w-24 p-2">
            Shot
          </div>
          {allMaterialIds.map((mid) => (
            <div key={mid} role="columnheader" className="w-20 p-2 text-center">
              {mid}
            </div>
          ))}
        </div>

        {shots.map((shot) => (
          <div key={shot.shot_id} role="row" className="flex border-b text-xs">
            <div role="rowheader" className="w-24 p-2" title={anchorTexts[shot.shot_id]}>
              {shot.shot_id}
              {anchorTexts[shot.shot_id] && (
                <span className="block text-gray-400 truncate">
                  {anchorTexts[shot.shot_id]}
                </span>
              )}
            </div>
            {allMaterialIds.map((mid) => {
              const mat = materialMap.get(mid);
              const inShot =
                mat &&
                mat.shot_id === shot.shot_id &&
                (shot.required_materials.includes(mid) ||
                  shot.optional_materials.includes(mid));
              const status = inShot && mat ? mat.verification_status : "pending";

              return (
                <div
                  key={mid}
                  role="gridcell"
                  data-testid={`cell-${shot.shot_id}-${mid}`}
                  data-status={status}
                  aria-label={STATUS_LABELS[status]}
                  className={`w-20 p-2 text-center border ${STATUS_STYLES[status]} cursor-pointer`}
                  onClick={() => {
                    if (inShot && mat) {
                      if (mat.verification_status === "missing") {
                        onRequestRefetch(mat.material_id);
                      }
                      if (mat.material_type === "chart") {
                        onRequestChange(mat.material_id);
                      }
                      setSelectedMaterial(mat);
                    }
                  }}
                >
                  {inShot ? status : "-"}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {selectedMaterial && (
        <MaterialDetailDrawer
          materialId={selectedMaterial.material_id}
          status={selectedMaterial.verification_status}
          rationale=""
          source=""
          evidence=""
          onRequestRefetch={onRequestRefetch}
          onClose={() => setSelectedMaterial(null)}
        />
      )}
    </div>
  );
}
