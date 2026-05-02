export interface Project {
  id: string;
  title: string;
  category: string;
  currentPhase: number; // 0 - 11
  progress: number; // 0 - 100
  status: 'in_progress' | 'awaiting_user' | 'completed' | 'failed';
  updatedAt: string;
}

export const PHASES = [
  'P0 需求定义',
  'P1 内容主线',
  'P2 口播脚本(结构化)',
  'P3 口播脚本(润色)',
  'P4 人声旁白',
  'P5 背景音乐',
  'P6 音效设计',
  'P7 分镜脚本',
  'P8 分镜物料补充',
  'P9 关键画面渲染',
  'P10 B-Roll 素材准备',
  'P11 粗剪合成',
  'P12 精剪交付',
];
