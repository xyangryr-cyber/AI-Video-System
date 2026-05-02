import React, { useState } from 'react';
import { RouteType } from '../App';
import { PHASES } from '../types';
import { ArrowLeft, CheckCircle2, Circle, Clock, MessageSquare, PlayCircle, Loader2, ExternalLink, ShieldCheck, AlertCircle, Search } from 'lucide-react';
import * as PhaseViews from '../components/PhaseViews';

interface ProjectWorkflowProps {
  projectId: string | null;
  onNavigate: (route: RouteType, projectId?: string) => void;
}

export default function ProjectWorkflow({ projectId, onNavigate }: ProjectWorkflowProps) {
  // Mock Factual Data for the sidebar
  const factualData = [
    {
      id: 'F1',
      content: '2025年第一季度全球央行净购金量为290吨',
      usage: 'S2E1 / P4 / P6',
      source: '世界黄金协会 (WGC)',
      link: 'https://www.gold.org/goldhub/data/gold-demand-trends',
      verified: true,
      method: '官方报告交叉验证'
    },
    {
      id: 'F2',
      content: 'LBMA 黄金现货价格 2024 年至今上涨约 12.5%',
      usage: 'S3E1 / P3',
      source: 'LBMA 实时报价接口',
      link: 'https://www.lbma.org.uk/prices-and-data',
      verified: true,
      method: 'API 通信指纹比对'
    },
    {
      id: 'F3',
      content: '美联储 2025 年 3 月放风维持利率不变',
      usage: 'P1 / 脚本背景',
      source: '美联储官网新闻稿',
      link: 'https://www.federalreserve.gov/newsevents.htm',
      verified: true,
      method: '文本语义一致性确认'
    }
  ];

  // Mock State
  const [currentPhase, setCurrentPhase] = useState(12); // Set max unlocked to 12 for testing
  const [viewingPhaseIndex, setViewingPhaseIndex] = useState(0); 
  const [isAwaitingUser, setIsAwaitingUser] = useState(true);
  const [showPreferenceModal, setShowPreferenceModal] = useState(false);
  const [showVeritasModal, setShowVeritasModal] = useState(false);
  const [hasNewFacts, setHasNewFacts] = useState(true); // Default to true for demo

  const renderPhaseView = () => {
    switch(viewingPhaseIndex) {
      case 0: return <PhaseViews.Phase0Requirements />;
      case 1: return <PhaseViews.Phase1Outline />;
      case 2: return <PhaseViews.Phase2ScriptOrig />;
      case 3: return <PhaseViews.Phase3Polished />;
      case 4: return <PhaseViews.Phase4Voice />;
      case 5: return <PhaseViews.Phase5BGM />;
      case 6: return <PhaseViews.Phase6SFX />;
      case 7: return <PhaseViews.Phase7Storyboard />;
      case 8: return <PhaseViews.Phase8AssetSourcing />;
      case 9: return <PhaseViews.Phase9Keyframes />;
      case 10: return <PhaseViews.Phase10BRoll />;
      case 11: return <PhaseViews.Phase11RoughCut />;
      case 12: return <PhaseViews.Phase12Final />;
      default: return <PhaseViews.Phase0Requirements />;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-[#f8fafc] overflow-hidden p-4 sm:p-5 gap-5 text-[#1e293b]">
      {/* Top Navigation */}
      <header className="h-16 bg-white border-2 border-slate-200 rounded-2xl flex items-center justify-between px-5 shrink-0 z-10 relative">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => onNavigate('list')}
            className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-md transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="font-medium text-slate-800">
            黄金价格走势分析与投资展望 <span className="text-slate-400 font-normal ml-2 text-sm">proj_001</span>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden gap-4">
        
        {/* Left: Compact Phase Navigation */}
        <aside className="w-16 bg-white border-2 border-slate-200 rounded-2xl flex flex-col items-center py-6 shrink-0 hidden md:flex shadow-sm">
          <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest vertical-rl rotate-180 mb-6 flex items-center gap-2">
             <div className="w-1 h-1 rounded-full bg-slate-300"></div>
             工作推进
             <div className="w-1 h-1 rounded-full bg-slate-300"></div>
          </div>
          <div className="flex-1 w-full flex flex-col items-center gap-4 overflow-y-auto no-scrollbar py-2">
            {PHASES.map((_, index) => {
              const isCompleted = index < currentPhase;
              const isActive = index === viewingPhaseIndex;
              const isCurrent = index === currentPhase;
              
              return (
                <button
                  key={index}
                  onClick={() => setViewingPhaseIndex(index)}
                  className={`group relative w-10 h-10 flex items-center justify-center rounded-xl transition-all
                    ${isActive ? 'bg-[#1e293b] text-white shadow-lg scale-110' : 'text-slate-400 hover:bg-slate-100'}
                    ${isCurrent && !isActive ? 'border-2 border-dashed border-blue-400' : ''}
                  `}
                >
                  <span className={`text-[11px] font-black ${isActive ? 'opacity-100' : 'opacity-60 group-hover:opacity-100'}`}>
                    P{index}
                  </span>
                  
                  {/* Tooltip hint */}
                  <div className="absolute left-full ml-3 px-2 py-1 bg-[#1e293b] text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity font-bold uppercase tracking-wider shadow-xl">
                    {PHASES[index]}
                  </div>

                  {/* Status dot */}
                  {isCompleted && (
                    <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white shadow-sm"></div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Global Feature: Factual Data Ledger */}
          <div className="mt-auto py-6 border-t border-slate-100 w-full flex flex-col items-center gap-4">
            <button
              onClick={() => {
                setShowVeritasModal(true);
                setHasNewFacts(false);
              }}
              className={`group relative w-10 h-10 flex items-center justify-center rounded-xl transition-all
                ${showVeritasModal ? 'bg-blue-600 text-white shadow-lg scale-110' : 'bg-slate-50 text-slate-400 hover:bg-slate-200'}
              `}
              title="事实清单 (Veritas)"
            >
              <ShieldCheck className={`w-5 h-5 ${showVeritasModal ? 'text-white' : 'text-slate-500'}`} />
              
              {hasNewFacts && (
                <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-white animate-pulse"></span>
              )}

              {/* Tooltip hint */}
              <div className="absolute left-full ml-3 px-2 py-1 bg-[#1e293b] text-white text-[10px] rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity font-bold uppercase tracking-wider shadow-xl">
                事实清单 (Veritas)
              </div>
            </button>
          </div>
        </aside>

        {/* Center: Dialog (Main Pillar - Full Height) */}
        <main className="flex-1 flex flex-col min-w-0 z-10 bg-white border-2 border-slate-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 bg-white flex justify-between items-center shrink-0">
             <h3 className="text-[0.8rem] font-black text-[#1e293b] uppercase tracking-[0.1em] flex items-center">
                <MessageSquare className="w-4 h-4 mr-2 text-blue-600" />
                协作对话终端 / {PHASES[viewingPhaseIndex]}
             </h3>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30">
            {/* Agent Message */}
            <div className="flex space-x-4 max-w-[90%]">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#1e293b] to-[#0f172a] flex items-center justify-center shrink-0 shadow-md">
                <div className="w-5 h-5 bg-white/20 rounded-lg backdrop-blur-sm"></div>
              </div>
              <div className="space-y-3">
                <div className="bg-white border-2 border-slate-200/60 rounded-2xl rounded-tl-sm px-5 py-4 text-sm text-slate-700 shadow-sm leading-relaxed">
                  <p className="font-medium text-slate-900 mb-1">VideoEngine Agent:</p>
                  <p>我已经根据大纲生成了第 2 版结构化脚本。我注意到您提到了"更口语化一些，不要像背研报"，已经在第二段做了相应调整。</p>
                  <div className="mt-4 p-3 bg-green-50/50 border border-green-100 rounded-xl flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center shrink-0">
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-[11px] font-bold text-green-800">FactChecker 验证通过</p>
                      <p className="text-[10px] text-green-600/80">3/3 核心数据已成功溯源至 Veritas 事实清单</p>
                    </div>
                  </div>
                </div>
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest pl-1">10:24 AM</div>
              </div>
            </div>

             {/* User Message */}
             <div className="flex space-x-4 justify-end">
              <div className="max-w-[85%] flex flex-col items-end gap-2">
                <div className="bg-[#1e293b] rounded-2xl rounded-tr-sm px-5 py-4 text-sm text-white shadow-lg leading-relaxed font-medium">
                  看起来不错，继续推进吧
                </div>
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest pr-1">10:25 AM</div>
              </div>
              <div className="w-10 h-10 rounded-xl bg-blue-100 border-2 border-blue-200 flex items-center justify-center shrink-0 shadow-sm">
                <span className="text-xs font-black text-blue-700">ME</span>
              </div>
            </div>

            {/* Preference Modal Card (embedded in flow) */}
            {showPreferenceModal && (
              <div className="bg-gradient-to-br from-indigo-50 to-white border-2 border-indigo-200 rounded-2xl p-6 shadow-xl max-w-xl mx-auto my-8 relative overflow-hidden group">
                <div className="absolute top-0 right-0 p-8 opacity-5">
                   <ShieldCheck className="w-24 h-24 text-indigo-900" />
                </div>
                <h3 className="font-black text-[#1e293b] uppercase tracking-wider text-sm mb-4 flex items-center">
                  <span className="w-2 h-2 rounded-full bg-indigo-500 mr-2 animate-ping"></span>
                  AI 记忆同步中
                </h3>
                <p className="text-[13px] text-slate-600 mb-5 leading-relaxed">
                  基于您上个步骤的反馈，Agent 学习到了新的内容生产规则：
                </p>
                <div className="bg-white p-4 rounded-xl border border-indigo-100 shadow-sm mb-6 flex gap-4">
                  <input type="checkbox" defaultChecked className="mt-1 w-5 h-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" />
                  <div>
                    <p className="font-bold text-slate-900 text-sm">强制标注事实出处</p>
                    <p className="text-xs text-slate-500 mt-1">"所有涉及金融指标的数据引用必须同时注明机构名称，禁止使用模糊指代。"</p>
                  </div>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <div className="flex gap-4">
                     <label className="flex items-center text-[10px] font-bold text-slate-500 uppercase cursor-pointer hover:text-indigo-600">
                        <input type="radio" name="scope" className="mr-1.5" /> 仅单次
                     </label>
                     <label className="flex items-center text-[10px] font-bold text-slate-500 uppercase cursor-pointer hover:text-indigo-600">
                        <input type="radio" name="scope" defaultChecked className="mr-1.5" /> 永久存储
                     </label>
                  </div>
                  <div className="flex gap-3">
                    <button onClick={() => setShowPreferenceModal(false)} className="px-4 py-2 text-[11px] font-bold text-slate-400 uppercase tracking-widest hover:text-red-500">关闭</button>
                    <button onClick={() => {
                        setShowPreferenceModal(false);
                        setCurrentPhase(3);
                        setIsAwaitingUser(false);
                    }} className="px-5 py-2.5 bg-[#1e293b] text-white rounded-xl text-[11px] font-bold uppercase tracking-widest shadow-lg hover:shadow-indigo-200 transition-all">
                      确认并进入下一阶段
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sticky Input Area */}
          <div className="p-5 bg-white border-t border-slate-100 shrink-0">
            <div className="relative group shadow-sm hover:shadow-md transition-shadow">
              <textarea
                className="w-full bg-slate-50 border-2 border-slate-100 rounded-2xl px-5 py-4 text-sm focus:outline-none focus:border-blue-400 focus:bg-white resize-none transition-all pr-32"
                rows={2}
                placeholder="对当前产物提出修改方案..."
              ></textarea>
              <div className="absolute right-3 bottom-3 flex items-center gap-2">
                 <button className="bg-[#1e293b] text-white rounded-xl px-4 py-2 text-[11px] font-bold uppercase tracking-widest hover:bg-black transition-colors">
                   发送反馈
                 </button>
              </div>
            </div>

            <div className="mt-5 flex justify-between items-center">
               <div className="flex items-center gap-4">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest leading-none mb-1">GateKeeper</span>
                    <span className="text-[11px] font-bold text-green-600 flex items-center">
                      <ShieldCheck className="w-3.5 h-3.5 mr-1" /> 所有准入审核已通过
                    </span>
                  </div>
               </div>
               <button 
                onClick={() => setShowPreferenceModal(true)}
                disabled={!isAwaitingUser}
                className={`flex items-center px-8 py-3 rounded-2xl text-[11px] font-black uppercase tracking-[0.15em] transition-all shadow-xl
                  ${isAwaitingUser ? 'bg-gradient-to-r from-blue-700 to-indigo-700 text-white hover:scale-[1.02]' : 'bg-slate-100 text-slate-400 cursor-not-allowed text-[10px]'}`}
               >
                 {isAwaitingUser ? '确认进入下一阶段' : '正在处理中...'}
                 <ArrowLeft className="w-full h-4 ml-3 rotate-180" />
               </button>
            </div>
          </div>
        </main>

        {/* Right: Artifact Preview & Agent Intelligence (Stacked) */}
        <aside className="w-[320px] lg:w-[480px] flex flex-col min-w-0 h-full gap-4 pb-1 overflow-hidden">
          
          {/* Artifact Preview */}
          <section className="flex-1 bg-white border-2 border-slate-200 rounded-2xl flex flex-col min-h-0 overflow-hidden shadow-sm relative group">
            <div className="px-5 py-3 border-b border-slate-100 bg-white flex justify-between items-center shrink-0">
              <h2 className="text-[0.7rem] font-black text-[#1e293b] uppercase tracking-[0.15em] flex items-center">
                <span className="w-2.5 h-2.5 rounded-sm bg-blue-600 mr-2"></span>
                P{viewingPhaseIndex} / 阶段产物预览
              </h2>
              <div className="flex gap-2">
                 <span className="text-[10px] font-mono font-black text-blue-600 bg-blue-50 px-2 py-0.5 rounded">V2</span>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5 bg-[#fcfcfc]">
               {renderPhaseView()}
            </div>
          </section>

          {/* Agent Task Ledger */}
          <div className="p-5 bg-white border-2 border-slate-200 rounded-2xl shrink-0 shadow-sm">
             <div className="flex justify-between items-center mb-4">
               <h4 className="text-[0.75rem] font-black text-[#1e293b] uppercase tracking-widest">任务监听器 (Stage Monitor)</h4>
               <span className="text-[9px] bg-slate-100 text-slate-500 font-bold px-2 py-0.5 rounded uppercase font-mono">Real-time</span>
             </div>
             
             <div className="space-y-3 relative">
                <div className="absolute left-3 top-2 bottom-4 w-px bg-slate-100 z-0"></div>

                <div className="relative z-10 flex items-start">
                  <div className="w-6 h-6 rounded-full bg-green-100 border-2 border-green-200 flex items-center justify-center shrink-0 mr-3">
                     <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                  </div>
                  <div className="flex-1 bg-slate-50/50 p-2.5 rounded-xl border border-slate-100 shadow-sm">
                    <div className="text-[11px] font-bold text-slate-800">生成口播脚本初版 (v1)</div>
                    <div className="text-[9px] text-slate-400 mt-0.5 uppercase tracking-tighter">ScriptAgent / 完成</div>
                  </div>
                </div>

                <div className="relative z-10 flex items-start">
                  <div className="w-6 h-6 rounded-full bg-blue-100 border-2 border-blue-200 flex items-center justify-center shrink-0 mr-3 shadow-sm ring-4 ring-blue-50">
                     <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse"></div>
                  </div>
                  <div className="flex-1 bg-blue-50/30 p-2.5 rounded-xl border border-blue-100 shadow-sm lg:border-l-4 lg:border-l-blue-600">
                    <div className="text-[11px] font-bold text-blue-900">用户反馈解析 & 修改重写 (v2)</div>
                    <div className="text-[9px] text-blue-500 mt-0.5 italic">"更口语化一些..."</div>
                  </div>
                </div>

                <div className="relative z-10 flex items-start">
                  <div className="w-6 h-6 rounded-full bg-slate-100 border-2 border-slate-200 flex items-center justify-center shrink-0 mr-3">
                     <Clock className="w-3.5 h-3.5 text-slate-400" />
                  </div>
                  <div className="flex-1 bg-slate-50/30 p-2.5 rounded-xl border border-slate-100 opacity-60">
                    <div className="text-[11px] font-bold text-slate-600 italic">FactChecker 最终审核</div>
                    <div className="text-[9px] text-slate-400 mt-0.5">待 v2 完成后自动触发</div>
                  </div>
                </div>
             </div>
          </div>
        </aside>
      </div>

      {/* Veritas Ledger Modal (Read-only) */}
      {showVeritasModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
           {/* Backdrop */}
           <div 
            className="absolute inset-0 bg-slate-900/60 backdrop-blur-md transition-opacity"
            onClick={() => setShowVeritasModal(false)}
           ></div>
           
           {/* Modal Content */}
           <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden animate-in fade-in zoom-in duration-200 border border-slate-100">
              <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                 <div>
                    <h3 className="text-2xl font-black text-[#1e293b] uppercase tracking-tighter flex items-center">
                       <ShieldCheck className="w-6 h-6 mr-3 text-blue-600" />
                       项目事实数据清单
                    </h3>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">Veritas / 溯源控制中心</p>
                 </div>
                 <button 
                  onClick={() => setShowVeritasModal(false)}
                  className="p-3 hover:bg-slate-200 rounded-2xl text-slate-600 transition-colors bg-slate-100"
                 >
                    <ArrowLeft className="w-6 h-6 rotate-180" />
                 </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 space-y-6">
                 {factualData.map((fact) => (
                    <div key={fact.id} className="p-6 bg-slate-50/50 border-2 border-slate-100 rounded-3xl relative overflow-hidden">
                       <div className="flex justify-between items-center mb-4">
                          <span className="bg-[#1e293b] text-white text-[11px] font-black px-3 py-1 rounded-lg">ID: {fact.id}</span>
                          <div className="px-3 py-1 rounded-full border border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px] font-black uppercase flex items-center">
                             <ShieldCheck className="w-3.5 h-3.5 mr-1" /> 已核实
                          </div>
                       </div>
                       
                       <div className="text-lg font-bold text-slate-800 leading-relaxed mb-6">
                          {fact.content}
                       </div>

                       <div className="grid grid-cols-2 gap-6 pt-6 border-t border-slate-200/50">
                          <div>
                             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">数据来源</span>
                             <div className="flex items-center text-xs font-bold text-slate-600">
                                <ExternalLink className="w-4 h-4 mr-2 text-blue-500" />
                                {fact.source}
                             </div>
                          </div>
                          <div>
                             <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">核实方法</span>
                             <div className="text-xs font-bold text-slate-600 flex items-center gap-2">
                                <Search className="w-4 h-4 text-amber-500" />
                                {fact.method}
                             </div>
                          </div>
                       </div>
                    </div>
                 ))}
                 
                 <div className="p-6 bg-blue-600 rounded-3xl text-white mt-4 relative overflow-hidden group">
                    <div className="relative z-10">
                       <h5 className="font-black text-xs uppercase tracking-widest mb-2">Veritas 实时审计中</h5>
                       <p className="text-sm leading-relaxed opacity-90">本项目所有事实数据均经过 AI 交叉验证，并锚定至官方发布源。如对数据有疑义，请在对话框中直接@FactChecker。</p>
                    </div>
                    <Search className="absolute -bottom-6 -right-6 w-32 h-32 opacity-20 rotate-12 group-hover:rotate-45 transition-transform duration-700" />
                 </div>
              </div>

              <div className="p-8 bg-slate-50 border-t border-slate-100 shrink-0">
                 <button 
                  onClick={() => setShowVeritasModal(false)}
                  className="w-full py-4 bg-[#1e293b] text-white rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl hover:bg-black transition-all"
                 >
                    关闭查阅界面
                 </button>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
