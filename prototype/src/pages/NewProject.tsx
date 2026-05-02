import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { RouteType } from '../App';

interface NewProjectProps {
  onNavigate: (route: RouteType, projectId?: string) => void;
}

export default function NewProject({ onNavigate }: NewProjectProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (description.length < 10) return;
    
    setIsSubmitting(true);
    // Simulate API call
    setTimeout(() => {
      onNavigate('workflow', 'new_proj_123');
    }, 800);
  };

  return (
    <div className="max-w-3xl mx-auto py-12 px-6">
      <button
        onClick={() => onNavigate('list')}
        className="flex items-center space-x-2 text-slate-500 hover:text-slate-900 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>返回列表</span>
      </button>

      <div className="bg-white rounded-2xl border-2 border-slate-200 p-8 shadow-sm">
        <h1 className="text-[1.25rem] font-bold tracking-tight text-[#1e293b] mb-2">新建视频项目</h1>
        <p className="text-slate-500 mb-8">用自然语言描述您的内容需求，AI Agent 将协助您完成视频制作全流程。</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-2">
              项目标题
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
              placeholder="例如：2025 Q4 黄金价格走势分析与投资展望"
              required
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-2">
              内容主题描述 (核心观点)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={8}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow py-2 resize-none"
              placeholder="请详细描述您的观点。例如：本期视频主要分析为什么黄金价格近期飙升，主要归因于各大央行增持以及地缘政治因素，适合作为中长期避险资产..."
              required
            />
            <div className="mt-2 text-xs flex justify-between">
              <span className={`${description.length > 0 && description.length < 10 ? 'text-red-500' : 'text-slate-500'}`}>
                至少 10 个字符
              </span>
              <span className="text-slate-400">{description.length} / 2000</span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              type="button"
              onClick={() => onNavigate('list')}
              className="px-6 py-2 text-slate-600 hover:bg-slate-100 rounded-lg font-medium mr-4 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting || description.length < 10 || !title.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isSubmitting ? '创建中...' : '开始制作'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
