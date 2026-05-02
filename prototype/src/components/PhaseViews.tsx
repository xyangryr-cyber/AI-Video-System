import React from 'react';
import { CheckCircle2, Volume2, ImageIcon, Video, FileText, Music, Sparkles, Download, Play, Mic, Waves, Clapperboard, MonitorPlay, MessageSquare, Clock } from 'lucide-react';

export const Phase0Requirements = () => (
  <div className="space-y-4">
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
        <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">主题 / 标题</div>
        <div className="text-sm font-medium text-slate-800">黄金价格走势分析与投资展望</div>
      </div>
      <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
        <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">分类定位</div>
        <div className="text-sm font-medium text-slate-800">金融财经 / 行业分析</div>
      </div>
      <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
        <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">目标受众时长</div>
        <div className="text-sm font-medium text-slate-800">Medium (约 8-12 分钟)</div>
      </div>
      <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
        <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider font-bold">发布平台策略</div>
        <div className="text-sm font-medium text-slate-800 flex gap-2 mt-1">
          <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-md text-xs">Bilibili (主)</span>
          <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md text-xs">Douyin (副)</span>
        </div>
      </div>
    </div>
    <div className="bg-white border-2 border-slate-200 rounded-xl p-4">
      <div className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-bold">核心提点与需求描述</div>
      <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
        本期视频主要分析为什么黄金价格近期飙升，主要归因于各大央行增持以及地缘政治因素，探讨其作为中长期避险资产的逻辑，需要数据支撑和通俗的比喻。
      </p>
    </div>
  </div>
);

export const Phase1Outline = () => (
  <div className="space-y-4">
    {[
      { title: '开头：抛出痛点与现象 (10%)', desc: '利用当前金价暴涨的热搜现象，吸引因踏空而焦虑的用户。' },
      { title: '第一部分：幕后推手是谁？ (35%)', desc: '列举第一季度多国央行狂买黄金的数据，解释去美元化与避险逻辑。' },
      { title: '第二部分：现在还能不能上车？ (40%)', desc: '区分短线风险与长线红利，给出实操建议（定投vs一把梭哈）。' },
      { title: '结尾：总结互动 (15%)', desc: '一句话口诀总结，并引导观众在评论区留下自己的仓位情况。' }
    ].map((item, i) => (
      <div key={i} className="flex gap-4 items-start bg-white border-2 border-slate-200 rounded-xl p-4 shadow-sm relative overflow-hidden">
        <div className="w-1 absolute left-0 top-0 bottom-0 bg-blue-500"></div>
        <div className="w-8 h-8 shrink-0 bg-blue-50 text-blue-600 font-bold rounded-lg flex items-center justify-center text-sm border border-blue-100">{i + 1}</div>
        <div>
          <h3 className="font-bold text-slate-800 text-sm mb-1">{item.title}</h3>
          <p className="text-sm text-slate-600">{item.desc}</p>
        </div>
      </div>
    ))}
  </div>
);

export const Phase2ScriptOrig = () => (
   <div className="space-y-5">
      <div className="bg-white border-2 border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="bg-slate-800 text-white px-4 py-2.5 text-sm font-bold flex justify-between tracking-wide">
          <span>段落 1: 开头-点题</span>
          <span className="text-slate-400 text-xs font-normal">约 120 字 • 30 秒</span>
        </div>
        <div className="p-4">
          <p className="text-slate-700 leading-relaxed text-[15px]">
            大家还记得去年这时候黄金才多少钱一克吗？现在是不是觉得高攀不起了？今天我们不聊虚的，直接来盘一盘这波黄金暴涨背后的核心推手，以及手头有闲钱的朋友，现在还能不能上车。
          </p>
          <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap gap-2 text-xs">
            <span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md font-medium"><span className="opacity-60 mr-1">情绪调性:</span> 好奇/引导</span>
          </div>
        </div>
      </div>

      <div className="bg-blue-50/50 border-2 border-blue-200 rounded-xl overflow-hidden shadow-sm relative ring-2 ring-blue-500 ring-offset-1">
        <div className="absolute top-2.5 right-2 flex space-x-2">
            <button className="text-[11px] bg-white text-blue-600 px-2 py-1 rounded-md border border-blue-100 shadow-sm hover:bg-blue-50 font-bold uppercase tracking-wider">重写此段</button>
        </div>
        <div className="bg-blue-900 text-white px-4 py-2.5 text-sm font-bold flex justify-between pr-24 tracking-wide">
          <span>段落 2: 核心上涨原因</span>
          <span className="text-blue-200 text-xs font-normal">约 180 字 • 45 秒</span>
        </div>
        <div className="p-4">
          <p className="text-slate-700 leading-relaxed text-[15px]">
            其实这波黄金上涨，散户买首饰那点量根本排不上号。主力军是谁？是各国央行。<span className="bg-amber-100 px-1 py-0.5 rounded cursor-help relative group underline decoration-amber-300 decoration-dotted underline-offset-4">世界黄金协会数据显示，2025年第一季度全球央行净购金量达到了创纪录的290吨
              <span className="hidden group-hover:block absolute bottom-full left-0 mb-2 w-64 bg-slate-800 text-white text-xs p-2.5 rounded-lg shadow-xl z-50">
                <strong className="text-slate-300">来源:</strong> 世界黄金协会 2025Q1 报告<br/>
                <span className="text-green-400 flex items-center mt-1"><CheckCircle2 className="w-3 h-3 mr-1"/> FactChecker 验证通过</span>
              </span>
            </span>。这个买盘力量是非常恐怖的，直接构筑了金价的坚固底座。
          </p>
          <div className="mt-4 pt-4 border-t border-blue-100/50">
            <h4 className="text-[11px] font-bold text-slate-500 mb-2 flex items-center uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4 text-green-500 mr-1.5" /> 关键数据点核查
            </h4>
            <div className="bg-white rounded-lg border border-slate-200 p-2.5 text-xs flex justify-between items-center shadow-sm">
              <div>
                <span className="font-bold text-slate-700">"央行净购金量290吨"</span>
                <span className="text-slate-400 ml-2">世界黄金协会 2025Q1 报告</span>
              </div>
              <span className="text-green-700 bg-green-100 border border-green-200 px-2 py-0.5 rounded-md font-bold text-[10px] tracking-wider uppercase">Verified</span>
            </div>
          </div>
        </div>
      </div>
  </div>
);

export const Phase3Polished = () => (
  <div className="bg-white border-2 border-slate-200 rounded-xl p-5">
    <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
      <div className="flex space-x-2">
        <span className="bg-purple-100 text-purple-700 px-2.5 py-1 rounded-md text-xs font-bold tracking-wider uppercase flex items-center shadow-sm">
          <Sparkles className="w-3.5 h-3.5 mr-1.5"/> Style Applied: 亲切科普型
        </span>
      </div>
      <div className="text-xs text-slate-400 font-medium">总字数: 2450 / 预计 10分12秒</div>
    </div>
    <div className="prose prose-slate prose-sm max-w-none text-[15px] space-y-4">
      <p>
        大家还记得去年这时候，黄金才多少钱一克吗？现在再看看金价，是不是觉得有些“高攀不起”了？今天咱们不聊虚的，直接来盘一盘，这波黄金原地起飞的背后，到底是谁在推波助澜。另外，手头正好有闲钱的朋友最关心的——现在还能不能上车？
      </p>
      <p>
        其实啊，这波黄金大涨，靠咱们平时去金店买两件金首饰，那点量根本排不上号。真正的绝对主力是谁？<strong>是各国央行。</strong>
      </p>
      <p className="bg-amber-50 border-l-4 border-amber-400 pl-4 py-1 italic relative">
        <span className="absolute -left-20 top-1 text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">口语化优化</span>
        这里给大家摆一个骇人听闻的数据：根据世界黄金协会的最新报告，光是 2025 年第一季度，全球央行的净购金量居然达到了创纪录的 290 吨！这是什么概念？这就等于“国家队”在疯狂扫货，这个买盘力量是非常恐怖的，直接给现在的金价打下了一个牢不可破的底座。
      </p>
    </div>
  </div>
);

export const Phase4Voice = () => (
  <div className="space-y-4">
    <div className="flex justify-between items-end mb-2">
       <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">分段试听与干音确认</span>
    </div>
    {[
      { id: 1, duration: '0:30', cps: '4.0', status: 'ready' },
      { id: 2, duration: '0:45', cps: '4.2', status: 'ready' },
      { id: 3, duration: '1:12', cps: '3.8', status: 'ready', warn: true }
    ].map(seg => (
      <div key={seg.id} className={`flex items-center bg-white border-2 rounded-xl p-4 transition-shadow ${seg.warn ? 'border-amber-200 bg-amber-50/20' : 'border-slate-200'}`}>
        <button className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-colors shrink-0 shadow-md">
          <Play className="w-4 h-4 ml-0.5" />
        </button>
        <div className="mx-4 flex-1">
          <div className="flex items-end justify-between font-bold text-sm text-slate-800 mb-2">
            <span>段落 {seg.id} 音频</span>
            <span className="text-xs text-slate-500 font-mono">{seg.duration}</span>
          </div>
          {/* Mock Waveform */}
          <div className="h-6 flex items-center gap-[2px]">
             {Array.from({ length: 40 }).map((_, i) => (
               <div key={i} className="bg-slate-300 w-full rounded-full" style={{ height: `${Math.max(20, Math.random() * 100)}%` }}></div>
             ))}
          </div>
        </div>
        <div className="shrink-0 flex flex-col items-end">
          <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md uppercase tracking-wide">CPS: {seg.cps}</span>
          {seg.warn && <span className="text-[10px] text-amber-600 font-bold mt-1">语速略缓</span>}
        </div>
      </div>
    ))}
    
    <div className="mt-6 pt-5 border-t border-slate-200 flex justify-between items-center">
       <div className="text-sm font-bold text-slate-700 flex items-center">
          <CheckCircle2 className="w-4 h-4 text-green-500 mr-1.5" />
          全案干音 (VoiceOnly) 已生成完毕
       </div>
       <button className="flex items-center text-sm font-bold text-blue-600 bg-blue-50 border border-blue-100 px-4 py-2 rounded-lg hover:bg-blue-100 transition-colors">
         <Download className="w-4 h-4 mr-2" />
         下载完整干音版 (.wav)
       </button>
    </div>
  </div>
);

export const Phase5BGM = () => (
  <div className="space-y-6">
    {/* Mood Curve */}
    <div className="bg-white border-2 border-slate-200 rounded-xl p-5 shadow-sm">
      <h3 className="text-[0.85rem] font-bold tracking-widest uppercase text-slate-500 mb-4 flex items-center">
        <Waves className="w-4 h-4 mr-2 text-blue-500"/> 情感与能量曲线规划
      </h3>
      <div className="h-24 flex items-end gap-1 px-2 border-b border-l border-slate-200 pb-1">
        {['30%','40%','60%','80%','90%','70%','50%','60%'].map((h, i) => (
          <div key={i} className="flex-1 bg-gradient-to-t from-blue-100 to-blue-400 rounded-t-sm" style={{ height: h }}></div>
        ))}
      </div>
      <div className="flex justify-between text-[10px] text-slate-400 uppercase font-bold tracking-widest mt-2">
        <span>引入 (悬念)</span>
        <span>正文 (激昂)</span>
        <span>结尾 (平缓)</span>
      </div>
    </div>

    {/* Tracks */}
    <div className="bg-white border-2 border-slate-200 rounded-xl overflow-hidden shadow-sm">
       <div className="p-4 border-b border-slate-100 flex items-center justify-between">
         <div className="flex items-center">
            <Music className="w-8 h-8 p-1.5 bg-indigo-100 text-indigo-600 rounded-lg mr-3" />
            <div>
              <div className="text-sm font-bold text-slate-800">全局配乐混合试听 (BGM + Voice)</div>
              <div className="text-xs text-slate-500 mt-0.5">主轨: Corporate Tech Cinematic</div>
            </div>
         </div>
       </div>
       <div className="p-4 bg-slate-50/50 flex flex-col gap-4">
         <div className="flex space-x-4 text-xs font-medium text-slate-600 border-b border-slate-200 pb-4">
           <div className="flex flex-col"><span className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">版权状态</span><span className="text-green-600 font-bold bg-green-100 px-2 py-0.5 rounded-md text-center max-w-fit">CC-BY (免版税)</span></div>
           <div className="flex flex-col"><span className="text-slate-400 text-[10px] uppercase tracking-wider mb-1">Ducking 包络</span><span className="font-bold">正文段自动避让 -18dB</span></div>
         </div>
         
         <div className="bg-slate-800 rounded-xl p-3 flex items-center">
            <button className="w-10 h-10 rounded-full bg-white text-slate-900 flex items-center justify-center hover:bg-slate-100 transition-colors shrink-0 shadow-md">
              <Play className="w-4 h-4 ml-0.5" />
            </button>
            <div className="mx-4 flex-1 h-8 flex items-center relative">
              {/* Mixed Waveform Mock */}
              <div className="absolute inset-0 flex items-center gap-[1px] opacity-40">
                {Array.from({ length: 60 }).map((_, i) => (
                  <div key={i} className="bg-indigo-300 w-full rounded-full" style={{ height: `${Math.max(10, Math.sin(i/5)*50 + 50)}%` }}></div>
                ))}
              </div>
              <div className="absolute inset-0 flex items-center gap-[1px]">
                {Array.from({ length: 60 }).map((_, i) => (
                   <div key={`v-${i}`} className="bg-white w-full rounded-full" style={{ height: `${Math.max(20, Math.random() * 80)}%` }}></div>
                ))}
              </div>
            </div>
            <div className="text-white text-xs font-mono font-bold tracking-wider">
               0:00 / 2:27
            </div>
         </div>
         
         <div className="flex justify-between items-center text-xs mt-1">
            <span className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-2 py-1 rounded-md font-bold flex items-center gap-1.5">
               <CheckCircle2 className="w-3.5 h-3.5" />
               Review Agent: 全局 BGM 与人声频段无冲突，情感起伏完美贴合
            </span>
            <button className="font-bold text-slate-500 hover:text-slate-800 underline underline-offset-4">更换配乐</button>
         </div>
       </div>
    </div>
    
    <div className="pt-2 border-t border-slate-200 flex justify-end items-center">
       <button className="flex items-center text-sm font-bold text-blue-600 bg-blue-50 border border-blue-100 px-4 py-2 rounded-lg hover:bg-blue-100 transition-colors shadow-sm">
         <Download className="w-4 h-4 mr-2" />
         下载混音初版 (.wav)
       </button>
    </div>
  </div>
);

export const Phase6SFX = () => (
  <div className="space-y-6">
    <div className="bg-white border-2 border-slate-200 rounded-xl p-5 shadow-sm">
       <h3 className="text-[0.85rem] font-bold tracking-widest uppercase text-slate-800 mb-2 border-b border-slate-100 pb-3">
          1. 全局音效布局规划 (脚本批注)
       </h3>
       <div className="prose prose-sm text-slate-700 max-w-none leading-loose">
          <p>
            大家还记得去年这时候，黄金才多少钱一克吗？<span className="relative group cursor-help inline-block">
               <span className="bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded border border-blue-200 mr-1 line-through decoration-slate-400">高攀不起</span>
               <Volume2 className="inline w-4 h-4 text-blue-600 -mt-1" />
               <span className="absolute hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-slate-800 text-white text-[11px] p-2.5 rounded-lg shadow-xl z-50 leading-snug">
                  <strong>音效:</strong> Whoosh (转场)<br/>
                  <span className="text-slate-300">理由: 情绪转折，强调现实落差感</span>
               </span>
            </span>了？今天咱们不聊虚的，直接来盘一盘，这波黄金原地起飞的背后，到底是谁在推波助澜。另外，手头正好有闲钱的朋友最关心的——现在还能不能上车？
          </p>
          <p>
            其实啊，这波黄金大涨，靠咱们平时去金店买两件金首饰，那点量根本排不上号。真正的绝对主力是谁？<strong>是各国央行。</strong>
          </p>
          <p>
            这里给大家摆一个骇人听闻的数据：根据世界黄金协会的最新报告，光是 2025 年第一季度，全球央行的净购金量居然达到了创纪录的 <span className="relative group cursor-help inline-block">
               <span className="bg-amber-100 text-amber-800 font-bold px-1.5 py-0.5 rounded border border-amber-200 mr-1">290吨！</span>
               <Volume2 className="inline w-4 h-4 text-amber-600 -mt-1" />
               <span className="absolute hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-slate-800 text-white text-[11px] p-2.5 rounded-lg shadow-xl z-50 leading-snug">
                  <strong>音效:</strong> Ding/Cash Register<br/>
                  <span className="text-slate-300">理由: 数据超预期，强化客观数据的敲击感与震撼力</span>
               </span>
            </span> 这是什么概念...
          </p>
       </div>
    </div>

    <div className="space-y-3">
      <h3 className="text-[0.85rem] font-bold tracking-widest uppercase text-slate-800 ml-1">
         2. 分段带反馈试听 (人声+BGM+SFX)
      </h3>
      {[
        { id: 1, sfxInfo: 'Whoosh x1' },
        { id: 2, sfxInfo: 'Ding x1, Risers x1' },
      ].map((seg) => (
        <div key={seg.id} className="flex items-center bg-white border-2 border-slate-200 rounded-xl p-4 transition-shadow hover:border-blue-300">
          <button className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 transition-colors shrink-0 shadow-md">
            <Play className="w-4 h-4 ml-0.5" />
          </button>
          <div className="mx-4 flex-1">
            <div className="flex items-end justify-between font-bold text-sm text-slate-800 mb-2">
              <span>Segment {seg.id} (混音预览)</span>
            </div>
            {/* Mock Waveform */}
            <div className="h-4 flex items-center gap-[2px]">
               {Array.from({ length: 30 }).map((_, i) => (
                 <div key={i} className="bg-slate-300 w-full rounded-full" style={{ height: `${Math.max(20, Math.random() * 100)}%` }}></div>
               ))}
               <div className="absolute w-1 h-6 bg-red-400 rounded left-[30%]" title="SFX Trigger Point"></div>
            </div>
          </div>
          <div className="shrink-0 flex flex-col items-end">
             <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md uppercase tracking-wide border border-slate-200">{seg.sfxInfo}</span>
          </div>
        </div>
      ))}
    </div>

    <div className="pt-2 border-t border-slate-200 flex justify-end items-center">
       <button className="flex items-center text-sm font-bold text-blue-600 bg-blue-50 border border-blue-100 px-4 py-2 rounded-lg hover:bg-blue-100 transition-colors shadow-sm">
         <Download className="w-4 h-4 mr-2" />
         下载复合音频版 (.wav)
       </button>
    </div>
  </div>
);

export const Phase7Storyboard = () => {
  const storyboardData = [
    { 
      id: 'S1E1', 
      time: '00:00 - 00:08', 
      script: '大家还记得去年这时候，黄金才多少钱一克吗？现在再看看...', 
      visualType: 'B-Roll', 
      visual: '散户在金店看金饰的困惑表现实拍', 
      info: '主标题：金价暴涨，你踏空了吗？', 
      effect: '淡入黑显，轻微画面拉伸推镜头' 
    },
    { 
      id: 'S1E2', 
      time: '00:08 - 00:15', 
      script: '今天咱们不聊虚的，直接来盘一盘这背后的主力到底是谁。', 
      visualType: 'Template', 
      visual: '华尔街金库金砖堆叠3D动画', 
      info: '无额外文字，展示纯净视觉', 
      effect: '光影扫过金砖边缘，转场特效' 
    },
    { 
      id: 'S2E1', 
      time: '00:15 - 00:30', 
      script: '世界黄金协会的最新报告，全球央行净购金量达到了创纪录的290吨！', 
      visualType: 'Template', 
      visual: '各国央行购金对比体量柱状图', 
      info: '高亮显示“290吨”数据，大字标红', 
      effect: '数据柱状体依次飞入，最后加粗弹跳' 
    },
    { 
      id: 'S3E1', 
      time: '00:30 - 00:45', 
      script: '这个买盘力量是非常恐怖的，直接构筑了金价的坚固底座。', 
      visualType: 'B-Roll', 
      visual: '大盘曲线一路上扬的宏观混剪记录', 
      info: '展示上升箭头图腾', 
      effect: '叠化转场，背景粒子上升特效' 
    },
  ];

  return (
    <div className="relative border-l-2 border-slate-200 ml-4 pl-8 space-y-6 pb-4 pt-2">
      {storyboardData.map((item) => (
        <div key={item.id} className="relative">
          {/* Timeline dot centered on the border */}
          <div className="absolute -left-[39.5px] top-4 w-4 h-4 rounded-full bg-white border-[3px] border-blue-500 shadow-sm z-10"></div>
          
          <div className="bg-white border-2 border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 hover:border-blue-300 transition-colors">
            {/* Header */}
            <div className="flex flex-wrap md:flex-nowrap justify-between gap-3 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-3">
                <span className="bg-[#1e293b] text-white font-bold px-2 py-0.5 rounded text-xs tracking-widest">{item.id}</span>
                <span className="font-mono text-slate-500 text-[13px] font-bold">{item.time}</span>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider uppercase border shrink-0 ${item.visualType==='Template' ? 'bg-blue-50 text-blue-600 border-blue-200' : 'bg-emerald-50 text-emerald-600 border-emerald-200'}`}>
                {item.visualType}
              </span>
            </div>

            {/* Content Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="space-y-4">
                <div>
                  <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                     <MessageSquare className="w-3.5 h-3.5 mr-1" /> 对应口播 (Script)
                  </h4>
                  <p className="text-[13px] text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100 italic leading-relaxed">"{item.script}"</p>
                </div>
                <div>
                  <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                     <MonitorPlay className="w-3.5 h-3.5 mr-1" /> 视频画面 (Visual)
                  </h4>
                  <p className="text-sm font-bold text-slate-800">{item.visual}</p>
                </div>
              </div>
              <div className="space-y-4 md:border-l md:border-slate-100 md:pl-5">
                <div>
                  <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                     <FileText className="w-3.5 h-3.5 mr-1" /> 展示信息 (Info)
                  </h4>
                  <p className="text-[13px] font-medium text-slate-600">{item.info}</p>
                </div>
                <div>
                  <h4 className="flex items-center text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-2">
                     <Sparkles className="w-3.5 h-3.5 mr-1" /> 动画/特效 (Effects)
                  </h4>
                  <p className="text-[13px] font-medium text-slate-600">{item.effect}</p>
                </div>
              </div>
            </div>
            
            {/* Action Bar */}
            <div className="pt-3 border-t border-slate-100 flex justify-end mt-2">
              <button className="text-xs text-blue-600 font-bold tracking-wide hover:bg-blue-50 px-4 py-2 rounded-lg transition-colors border border-transparent hover:border-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-100">
                针对 {item.id} 提修改要求
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export const Phase8AssetSourcing = () => {
  const storyboardData = [
    { 
      id: 'S1E1', 
      time: '00:00 - 00:08', 
      visualType: 'B-Roll', 
      visual: '散户在金店看金饰的困惑表现实拍', 
      assetStatus: 'not_needed',
      assetDetail: null
    },
    { 
      id: 'S1E2', 
      time: '00:08 - 00:15', 
      visualType: 'Template', 
      visual: '华尔街金库金砖堆叠3D动画', 
      assetStatus: 'not_needed',
      assetDetail: null
    },
    { 
      id: 'S2E1', 
      time: '00:15 - 00:30', 
      visualType: 'Template', 
      visual: '各国央行购金对比体量柱状图', 
      assetStatus: 'fetched',
      assetDetail: {
        need: '支撑“央行购金量创纪录290吨”的准确年份与趋势数据',
        action: 'Search Web > WGC Q1 2025 Gold Demand Trends',
        data: '{ "source": "WGC", "Q1_Net_Purchases": "290t", "trend": "up" }'
      }
    },
    { 
      id: 'S3E1', 
      time: '00:30 - 00:45', 
      visualType: 'Template', 
      visual: '大盘曲线一路上扬的动画', 
      assetStatus: 'fetched',
      assetDetail: {
        need: '2024年初至今的金价走势折线图参考数据',
        action: 'API Fetch > LBMA Historical Prices',
        data: '{ "start": "2050 USD", "end": "2300 USD", "nodes": 12 }'
      }
    },
  ];

  return (
    <div className="relative border-l-2 border-slate-200 ml-4 pl-8 space-y-6 pb-4 pt-2">
      {storyboardData.map((item) => (
        <div key={item.id} className="relative">
          {/* Timeline dot centered on the border */}
          <div className="absolute -left-[39.5px] top-4 w-4 h-4 rounded-full bg-white border-[3px] border-blue-500 shadow-sm z-10"></div>
          
          <div className="bg-white border-2 border-slate-200 rounded-2xl p-5 shadow-sm hover:border-blue-300 transition-colors">
            {/* Header */}
            <div className="flex flex-wrap md:flex-nowrap justify-between gap-3 border-b border-slate-100 pb-3 mb-4">
              <div className="flex items-center gap-3">
                <span className="bg-[#1e293b] text-white font-bold px-2 py-0.5 rounded text-xs tracking-widest">{item.id}</span>
                <span className="font-mono text-slate-500 text-[13px] font-bold">{item.time}</span>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider uppercase border shrink-0 ${item.visualType==='Template' ? 'bg-blue-50 text-blue-600 border-blue-200' : 'bg-emerald-50 text-emerald-600 border-emerald-200'}`}>
                {item.visualType}
              </span>
            </div>

            <div className="mb-4">
               <span className="text-[13px] font-bold text-slate-700">画面规划：</span>
               <span className="text-[13px] text-slate-600 ml-1">{item.visual}</span>
            </div>

            {item.assetStatus === 'not_needed' ? (
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 flex items-center text-[12px] text-slate-500">
                <CheckCircle2 className="w-4 h-4 mr-2" /> 无需额外动态数据源，将使用常规素材库
              </div>
            ) : (
              <div className="border border-blue-100 bg-blue-50/30 rounded-xl p-4 relative">
                 <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                      <span className="text-[12px] font-bold text-slate-800">AI Agent 物料溯源结果</span>
                    </div>
                    <span className="text-[10px] text-green-700 font-bold border border-green-200 bg-green-100 flex items-center px-2 py-0.5 rounded shadow-sm">
                       <CheckCircle2 className="w-3 h-3 mr-1" /> Verified
                    </span>
                 </div>
                 
                 <div className="space-y-2 mt-3">
                   <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-2">
                     <span className="text-[11px] font-bold text-slate-500 w-16 shrink-0 mt-0.5 uppercase tracking-wide">Need:</span>
                     <span className="text-[12px] text-slate-700 font-medium">{item.assetDetail?.need}</span>
                   </div>
                   <div className="flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-2">
                     <span className="text-[11px] font-bold text-slate-500 w-16 shrink-0 mt-0.5 uppercase tracking-wide">Action:</span>
                     <span className="text-[12px] text-blue-700 bg-blue-100 px-2 py-0.5 rounded inline-block font-bold">{item.assetDetail?.action}</span>
                   </div>
                 </div>

                 <div className="mt-3 pt-3 border-t border-blue-100/50">
                    <div className="bg-[#1e293b] rounded-lg p-3 text-[11px] font-mono text-emerald-400 overflow-x-auto shadow-inner border border-slate-800">
                      {item.assetDetail?.data}
                    </div>
                 </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export const Phase9Keyframes = () => {
  const storyboardData = [
    { 
      id: 'S1E1', 
      time: '00:00 - 00:08', 
      visualType: 'B-Roll', 
      visual: '散户在金店看金饰的困惑表现实拍',
      renderStatus: 'pending_broll',
    },
    { 
      id: 'S1E2', 
      time: '00:08 - 00:15', 
      visualType: 'Template', 
      visual: '华尔街金库金砖堆叠3D动画', 
      renderStatus: 'rendered',
      fileName: 'Keyframe_S1E2.mp4'
    },
    { 
      id: 'S2E1', 
      time: '00:15 - 00:30', 
      visualType: 'Template', 
      visual: '各国央行购金对比体量柱状图', 
      renderStatus: 'rendered',
      fileName: 'Keyframe_S2E1.mp4'
    },
    { 
      id: 'S3E1', 
      time: '00:30 - 00:45', 
      visualType: 'Template', 
      visual: '大盘曲线一路上扬的动画', 
      renderStatus: 'rendered',
      fileName: 'Keyframe_S3E1.mp4'
    },
  ];

  return (
    <div className="relative border-l-2 border-slate-200 ml-4 pl-8 space-y-6 pb-4 pt-2">
      {storyboardData.map((item) => (
        <div key={item.id} className="relative">
          {/* Timeline dot centered on the border */}
          <div className="absolute -left-[39.5px] top-4 w-4 h-4 rounded-full bg-white border-[3px] border-blue-500 shadow-sm z-10"></div>
          
          <div className="bg-white border-2 border-slate-200 rounded-2xl overflow-hidden shadow-sm hover:border-blue-300 transition-colors flex flex-col sm:flex-row">
            
            {/* Left/Top Content: Timeline info */}
            <div className="p-5 sm:w-1/2 flex flex-col justify-between border-b sm:border-b-0 sm:border-r border-slate-100">
               <div>
                  <div className="flex flex-wrap md:flex-nowrap justify-between gap-3 pb-3 mb-3 border-b border-slate-100">
                    <div className="flex items-center gap-3">
                      <span className="bg-[#1e293b] text-white font-bold px-2 py-0.5 rounded text-xs tracking-widest">{item.id}</span>
                      <span className="font-mono text-slate-500 text-[13px] font-bold">{item.time}</span>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold tracking-wider uppercase border shrink-0 ${item.visualType==='Template' ? 'bg-blue-50 text-blue-600 border-blue-200' : 'bg-emerald-50 text-emerald-600 border-emerald-200'}`}>
                      {item.visualType}
                    </span>
                  </div>
                  <div className="text-[13px] text-slate-600">{item.visual}</div>
               </div>
               
               <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                 {item.renderStatus === 'rendered' ? (
                   <span className="text-[10px] text-green-700 font-bold border border-green-200 bg-green-100 flex items-center px-2 py-0.5 rounded shadow-sm uppercase tracking-wider">
                      <CheckCircle2 className="w-3 h-3 mr-1" /> Rendered
                   </span>
                 ) : (
                   <span className="text-[10px] text-amber-700 font-bold border border-amber-200 bg-amber-50 flex items-center px-2 py-0.5 rounded shadow-sm uppercase tracking-wider">
                      <Clock className="w-3 h-3 mr-1" /> Awaiting P10
                   </span>
                 )}
               </div>
            </div>

            {/* Right/Bottom Content: Video/Placeholder */}
            <div className="sm:w-1/2 relative bg-slate-50 flex items-center justify-center min-h-[160px] group">
               {item.renderStatus === 'rendered' ? (
                 <>
                   <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                      <div className="w-12 h-12 bg-black/40 backdrop-blur rounded-full flex items-center justify-center group-hover:bg-blue-600 transition-colors shadow-lg">
                        <Play className="w-5 h-5 text-white ml-1" />
                      </div>
                   </div>
                   <ImageIcon className="w-10 h-10 text-slate-300 absolute" />
                   <div className="absolute bottom-2 right-2 bg-slate-900/60 text-white text-[10px] px-2 py-0.5 rounded font-mono z-10">
                     {item.fileName}
                   </div>
                 </>
               ) : (
                 <div className="flex flex-col items-center justify-center text-slate-400 p-4 text-center">
                    <Video className="w-8 h-8 mb-2 opacity-50" />
                    <span className="text-[11px] font-bold uppercase tracking-wider">等待 B-Roll 库填充</span>
                 </div>
               )}
            </div>

          </div>
        </div>
      ))}
    </div>
  );
};

export const Phase10BRoll = () => (
  <div className="space-y-4">
    <div className="bg-white border-2 border-slate-200 p-4 rounded-xl flex items-start gap-4">
      <div className="w-32 aspect-video bg-slate-200 rounded-lg shrink-0 flex items-center justify-center text-slate-400 border border-slate-300">
        <Video className="w-6 h-6" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start mb-1">
          <div className="font-bold text-sm text-slate-800 truncate">broll_gold_bars.mp4</div>
          <span className="text-[10px] font-bold bg-slate-100 px-2 py-0.5 rounded border border-slate-200 shrink-0">15s</span>
        </div>
        <div className="text-xs text-slate-500 mb-2">匹配: "华尔街金库/金砖实拍"</div>
        <div className="text-[10px] font-bold uppercase tracking-wider text-green-600 bg-green-50 inline-block px-2 py-0.5 rounded-sm">Pexels (CC0)</div>
      </div>
    </div>
    <div className="bg-white border-2 border-slate-200 p-4 rounded-xl flex items-start gap-4">
       {/* More mocked videos can go here */}
       <div className="text-sm text-slate-500 p-4 text-center w-full">共匹配 5 段 B-Roll 素材，覆盖率 45%</div>
    </div>
  </div>
);

export const Phase11RoughCut = () => (
  <div className="space-y-4 flex flex-col h-full">
    <div className="bg-slate-900 border-2 border-slate-800 rounded-2xl aspect-video relative shadow-lg overflow-hidden shrink-0 flex items-center justify-center">
       <Clapperboard className="w-16 h-16 text-slate-700" />
       <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center cursor-pointer hover:bg-white/20 transition-colors backdrop-blur-sm border border-white/20">
            <Play className="w-6 h-6 text-white ml-1" />
          </div>
       </div>
       <div className="absolute bottom-4 right-4 bg-black/60 backdrop-blur text-white px-2 py-1 rounded text-xs font-mono font-bold tracking-wider">
         00:00 / 10:25
       </div>
    </div>
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-white border-2 border-slate-200 p-4 rounded-xl">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">AV Sync</div>
        <div className="text-sm font-bold text-green-600 flex items-center"><CheckCircle2 className="w-4 h-4 mr-1.5"/> 同步偏移 &lt; 50ms</div>
      </div>
      <div className="bg-white border-2 border-slate-200 p-4 rounded-xl">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Tracks Mixed</div>
        <div className="text-sm font-bold text-slate-700">Video + Audio + 字幕</div>
      </div>
    </div>
  </div>
);

export const Phase12Final = () => (
  <div className="space-y-5">
    <div className="bg-white border-2 border-slate-200 rounded-xl overflow-hidden p-1 shadow-sm">
      <div className="bg-slate-50 rounded-lg p-6 text-center border border-slate-100">
        <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 border-[3px] border-green-200 shadow-sm">
          <CheckCircle2 className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-1">视频精剪完成！</h3>
        <p className="text-slate-500 text-sm">项目《黄金价格走势分析与投资展望》已就绪</p>
      </div>
    </div>

    <div className="grid grid-cols-2 gap-4">
       <button className="bg-white border-2 border-slate-200 hover:border-blue-400 hover:bg-blue-50 transition-all rounded-xl p-4 flex flex-col items-center justify-center gap-3 text-center group">
         <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
           <Download className="w-5 h-5" />
         </div>
         <div>
           <div className="text-sm font-bold text-slate-800">下载 B 站版本</div>
           <div className="text-[10px] font-mono text-slate-500 mt-1">1080P | H.264 | 180MB</div>
         </div>
       </button>
       <button className="bg-white border-2 border-slate-200 hover:border-blue-400 hover:bg-blue-50 transition-all rounded-xl p-4 flex flex-col items-center justify-center gap-3 text-center group">
         <div className="w-10 h-10 bg-slate-100 text-slate-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
           <Download className="w-5 h-5" />
         </div>
         <div>
           <div className="text-sm font-bold text-slate-800">下载抖音版本</div>
           <div className="text-[10px] font-mono text-slate-500 mt-1">竖屏 | 1080x1920 | 165MB</div>
         </div>
       </button>
    </div>

    <div className="bg-white border-2 border-slate-200 rounded-xl p-4 flex justify-between items-center shadow-sm">
      <div className="flex items-center gap-3">
        <FileText className="w-5 h-5 text-slate-400" />
        <span className="text-sm font-bold text-slate-700">配套字幕文件 (SRT)</span>
      </div>
      <button className="text-blue-600 font-bold text-xs uppercase tracking-wider hover:underline underline-offset-4">Download</button>
    </div>
  </div>
);
