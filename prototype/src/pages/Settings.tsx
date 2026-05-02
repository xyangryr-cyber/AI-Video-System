import React, { useState } from 'react';
import { ArrowLeft, Save, Shield, HardDrive, Cpu, RefreshCw, FileText } from 'lucide-react';
import { RouteType } from '../App';

interface SettingsProps {
  onNavigate: (route: RouteType, projectId?: string) => void;
}

export default function Settings({ onNavigate }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<'api' | 'models' | 'preferences'>('api');

  const tabs = [
    { id: 'api', label: 'API 密钥配置', icon: Shield },
    { id: 'models', label: '模型与策略', icon: Cpu },
    { id: 'preferences', label: '偏好全局快照', icon: HardDrive },
  ] as const;

  return (
    <div className="max-w-4xl mx-auto py-12 px-6">
      <div className="flex items-center space-x-4 mb-8">
        <button
          onClick={() => onNavigate('list')}
          className="p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-semibold text-slate-900">系统设置</h1>
      </div>

      <div className="flex gap-5">
        {/* Nav sidebar inside settings */}
        <div className="w-64 shrink-0 bg-white border-2 border-slate-200 rounded-2xl p-4">
          <nav className="space-y-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-4 py-3 font-medium rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <tab.icon className="w-4 h-4 mr-3" /> {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content area */}
        {activeTab === 'api' && (
          <div className="flex-1 bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col">
             <div className="p-6 border-b border-slate-200 shrink-0">
               <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">API 密钥配置 (全局)</h2>
               <p className="text-sm text-slate-500 mt-1">应用环境变量配置界面。在私有化部署中，敏感配置写入背后 .env 文件中。</p>
             </div>
             
             <div className="p-6 space-y-6">
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">主 LLM 引擎 (Producer Agents)</label>
                    <select className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5">
                      <option>gemini-2.0-pro-exp-02-05</option>
                      <option>gemini-2.0-flash</option>
                    </select>
                  </div>
                  
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">主 LLM API Key</label>
                    <input type="password" value="**************" disabled className="w-full bg-slate-100 border border-slate-300 text-slate-600 text-sm rounded-lg block p-2.5 cursor-not-allowed" />
                    <p className="text-xs text-slate-400 mt-1">配置在运行时环境中，不可在此修改</p>
                  </div>

                  <div className="col-span-2">
                    <div className="border-t border-slate-100 my-4"></div>
                  </div>

                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">Intent Router 模型</label>
                    <select disabled className="w-full bg-slate-100 border border-slate-300 text-slate-600 text-sm rounded-lg block p-2.5 cursor-not-allowed">
                      <option>claude-3-5-haiku</option>
                    </select>
                    <p className="text-xs text-amber-600 mt-1 font-medium">V1 硬编码，保障 P95 延迟 ≤ 3s</p>
                  </div>

                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">TTS 提供商</label>
                    <select className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5">
                      <option>Edge TTS</option>
                      <option>ElevenLabs</option>
                      <option>Azure</option>
                    </select>
                  </div>
                </div>

                <div className="pt-6 border-t border-slate-100 flex justify-end">
                   <button className="flex items-center px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium shadow-sm transition-colors">
                     <Save className="w-4 h-4 mr-2" />
                     保存配置
                   </button>
                </div>
             </div>
          </div>
        )}

        {activeTab === 'models' && (
          <div className="flex-1 bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col">
             <div className="p-6 border-b border-slate-200 shrink-0">
               <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">模型与策略配置</h2>
               <p className="text-sm text-slate-500 mt-1">全局模型的生成控制、失败重试等任务编排调度策略。</p>
             </div>
             <div className="p-6 space-y-6 overflow-y-auto">
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">生成模型温度 (Temperature)</label>
                    <input type="range" min="0" max="1" step="0.1" defaultValue="0.7" className="w-full accent-blue-600" />
                    <div className="flex justify-between text-[11px] text-slate-400 mt-2">
                      <span>0.0 (更稳定)</span>
                      <span className="text-slate-600 font-medium bg-slate-100 px-2 py-0.5 rounded">当前: 0.7</span>
                      <span>1.0 (更有创意)</span>
                    </div>
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">任务失败最大重试次数 (max_attempts)</label>
                    <input type="number" defaultValue={3} min={1} max={5} className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5" />
                  </div>
                  <div className="col-span-2">
                    <div className="border-t border-slate-100 my-2"></div>
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">审核模型 (Reviewer Agents)</label>
                    <select className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5">
                      <option>gemini-2.0-flash</option>
                      <option>gemini-2.0-pro-exp-02-05</option>
                    </select>
                    <p className="text-xs text-slate-500 mt-1">负责通过各阶段门禁检查</p>
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-slate-700 mb-2">异步任务并发策略</label>
                    <select className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5">
                      <option>单线程串行 (V1 默认)</option>
                      <option disabled>多线程池 (V1.5+ 支持)</option>
                    </select>
                  </div>
                </div>
                <div className="pt-6 border-t border-slate-100 flex justify-end">
                   <button className="flex items-center px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium shadow-sm transition-colors">
                     <Save className="w-4 h-4 mr-2" /> 保存策略
                   </button>
                </div>
             </div>
          </div>
        )}

        {activeTab === 'preferences' && (
          <div className="flex-1 bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col">
             <div className="p-6 border-b border-slate-200 shrink-0 flex justify-between items-center bg-slate-50/50">
               <div>
                 <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">偏好全局快照 (snapshot.md)</h2>
                 <p className="text-sm text-slate-500 mt-1">只读导出视图，作为 Agent 下一阶段处理的参考事实核查与风格修正基准。</p>
               </div>
               <button className="flex items-center px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-sm font-medium transition-colors shadow-sm focus:ring-2 focus:ring-blue-500 outline-none">
                 <RefreshCw className="w-4 h-4 mr-1.5 text-slate-400" /> 重新导出
               </button>
             </div>
             <div className="p-6 overflow-y-auto flex-1 bg-slate-100 shadow-[inset_0_2px_10px_rgba(0,0,0,0.02)]">
               <div className="bg-white border border-slate-200 rounded-xl p-5 font-mono text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
{`# 全局制作规范 (Global Rules)
- 所有数据引用必须标注原始来源
- 不得使用具有明显偏见的过度情绪化表达，保持客观中立

# 跨项目长期偏好 (User Preferences)
- 开头第一段不要引用学术论文，用身边故事代入 (来源: proj_001)
- 讲解专有名词时，优先使用生活化比喻 (来源: proj_002)
- 喜欢节奏轻快的鼓点背景音乐 (来源: proj_001)

# 本项目滚动偏好 (Project Preferences)
- 本次视频语速需加快至 280字/分钟，因受限于短视频平台时长
- 所有数据引用必须同时注明机构名称，不要只写"有数据指出"
- 提及的黄金价格必须使用人民币计价 (来源: proj_001.phase_2)`}
               </div>
               <div className="mt-4 flex justify-end">
                 <button className="flex items-center text-sm text-blue-600 hover:text-blue-700 font-medium underline-offset-4 hover:underline">
                   <FileText className="w-4 h-4 mr-1.5" /> 导出并下载 snapshot.md
                 </button>
               </div>
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
