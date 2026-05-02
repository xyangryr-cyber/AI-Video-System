import React from 'react';
import { Plus, Settings, Play, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { RouteType } from '../App';
import { Project } from '../types';

interface ProjectListProps {
  onNavigate: (route: RouteType, projectId?: string) => void;
}

const mockProjects: Project[] = [
  {
    id: 'proj_001',
    title: '黄金价格走势分析与投资展望',
    category: '行业分析',
    currentPhase: 2,
    progress: 25,
    status: 'in_progress',
    updatedAt: '10 分钟前',
  },
  {
    id: 'proj_002',
    title: '十五五规划解读',
    category: '政策解读',
    currentPhase: 1,
    progress: 15,
    status: 'awaiting_user',
    updatedAt: '2 小时前',
  },
  {
    id: 'proj_003',
    title: '美联储加息影响',
    category: '时事解读',
    currentPhase: 11,
    progress: 100,
    status: 'completed',
    updatedAt: '昨天',
  },
];

export default function ProjectList({ onNavigate }: ProjectListProps) {
  const getStatusIcon = (status: Project['status']) => {
    switch (status) {
      case 'in_progress':
        return <Play className="w-4 h-4 text-blue-500" />;
      case 'awaiting_user':
        return <Clock className="w-4 h-4 text-amber-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusText = (status: Project['status']) => {
    switch (status) {
      case 'in_progress': return '进行中';
      case 'awaiting_user': return '等用户';
      case 'completed': return '完成';
      case 'failed': return '失败';
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-6">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">AI 视频制作系统</h1>
          <p className="text-sm text-slate-500 mt-1">面向金融内容创作者的专业工作流</p>
        </div>
        <div className="flex space-x-4">
          <button
            onClick={() => onNavigate('settings')}
            className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button
            onClick={() => onNavigate('new')}
            className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>新建项目</span>
          </button>
        </div>
      </header>

      <div className="bg-white rounded-2xl border-2 border-slate-200 p-6 flex flex-col gap-4">
        <h2 className="text-[0.85rem] font-bold text-slate-800 uppercase tracking-[0.05em]">M3: 项目管理列表</h2>
        <div className="overflow-x-auto border border-slate-200 rounded-xl">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">标题</th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">分类</th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">阶段</th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">进度</th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">状态</th>
                <th className="py-4 px-6 text-[0.75rem] font-bold text-slate-800 uppercase tracking-[0.05em]">更新时间</th>
              </tr>
            </thead>
          <tbody className="divide-y divide-slate-100">
            {mockProjects.map((project) => (
              <tr
                key={project.id}
                onClick={() => onNavigate('workflow', project.id)}
                className="hover:bg-slate-50 cursor-pointer transition-colors group"
              >
                <td className="py-4 px-6 font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                  {project.title}
                </td>
                <td className="py-4 px-6 text-sm text-slate-600">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                    {project.category}
                  </span>
                </td>
                <td className="py-4 px-6 text-sm text-slate-600">
                  Phase {project.currentPhase}
                </td>
                <td className="py-4 px-6">
                  <div className="flex items-center w-full max-w-[120px]">
                    <div className="w-full bg-slate-200 rounded-full h-1.5 flex-1 relative overflow-hidden">
                      <div
                        className="bg-blue-600 h-1.5 rounded-full absolute top-0 left-0"
                        style={{ width: `${project.progress}%` }}
                      ></div>
                    </div>
                  </div>
                </td>
                <td className="py-4 px-6">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(project.status)}
                    <span className="text-sm text-slate-600">{getStatusText(project.status)}</span>
                  </div>
                </td>
                <td className="py-4 px-6 text-sm text-slate-500 whitespace-nowrap">
                  {project.updatedAt}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
        {mockProjects.length === 0 && (
          <div className="py-12 text-center text-slate-500">
            暂无项目，点击右上角新建。
          </div>
        )}
      </div>
    </div>
  );
}
