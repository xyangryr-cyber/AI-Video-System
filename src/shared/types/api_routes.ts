// [SPEC-A-017] API route registry (additive).
//
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-5.
//
// This file is the TypeScript contract mirror for the v3.17 additions to
// the SPEC-1A route table. The full 25-endpoint registry is owned by
// SPEC-A-006 (still pending). This module only declares the v3.17 deltas
// and is designed to merge with the A-006 registry additively.

import type {
  GetMasterAudioRequest,
  GetMasterAudioResponse,
  MasterAudioErrorCode,
} from './api_master_audio';
import type { PhaseId } from './phase_enum';

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

export interface ApiRouteDef<Req, Resp, Err = never> {
  method: HttpMethod;
  path: string;
  // Declared for downstream code-gen / client SDK; empty marker interfaces.
  requestType?: Req;
  responseType?: Resp;
  errorCodes?: readonly Err[];
}

// v3.17 A-AUDP7A-5: master-audio endpoint.
export const GET_MASTER_AUDIO_ROUTE: ApiRouteDef<
  GetMasterAudioRequest,
  GetMasterAudioResponse,
  MasterAudioErrorCode
> = {
  method: 'GET',
  path: '/api/projects/{project_id}/artifacts/master_audio',
  errorCodes: ['invalid_phase', 'master_not_ready'],
} as const;

// v3.17 A-AUDP7A-5: v3.16 phase-detail endpoint gains `phase_7a` as a legal
// query-param value. The route path is owned by the v3.16 A-BDD-3 contract
// (SPEC-A-102); this entry re-declares the phase-parameter enum so callers
// importing from v3.17 get the extended set.
export const PHASE_DETAIL_QUERY_PHASE_ENUM: readonly PhaseId[] = [
  'P0', 'P1', 'P2', 'P3', 'P4', 'P5',
  'P6', 'P7', 'phase_7a', 'P8', 'P9', 'P10', 'P11',
] as const;

// Additive registry of v3.17 route deltas. Merges with SPEC-A-006's full
// table when that lands.
export const V317_ROUTE_DELTAS = {
  get_master_audio: GET_MASTER_AUDIO_ROUTE,
} as const;
