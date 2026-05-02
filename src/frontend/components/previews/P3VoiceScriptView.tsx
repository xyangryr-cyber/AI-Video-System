import type { VoiceDirection } from '@frontend/types/preview';
import { FileText, Sparkles } from 'lucide-react';

interface P3VoiceScriptViewProps {
  content?: string;
  voice_directions?: VoiceDirection[];
}

/** Estimate duration from char count (Chinese TTS ~4 chars/sec). */
function estimateDuration(charCount: number): string {
  const totalSec = Math.round(charCount / 4);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}分${sec}秒`;
}

export function P3VoiceScriptView({ content, voice_directions }: P3VoiceScriptViewProps) {
  if (!content) {
    return (
      <div data-testid="preview-p3" className="flex flex-col items-center justify-center h-64 text-slate-400">
        <FileText className="w-12 h-12 mb-2" />
        <p className="text-sm font-medium">暂无精修脚本内容</p>
        <p className="text-xs text-slate-400 mt-1">等待风格精修 Agent 完成口语化优化</p>
      </div>
    );
  }

  const tone = voice_directions?.[0]?.tone || '默认';
  const charCount = content.length;
  const duration = estimateDuration(charCount);

  // Check if any voice direction indicates oral-language optimization
  const hasOralOpt = voice_directions?.some(
    (vd) => vd.text?.includes('口语化'),
  ) || voice_directions?.some(
    (vd) => vd.notes?.includes('口语化') || vd.notes?.includes('energetic'),
  );

  // Split content into paragraphs
  const paragraphs = content.split(/\n+/).filter(Boolean);
  if (paragraphs.length === 0) paragraphs.push(content);

  return (
    <div
      data-testid="preview-p3"
      className="bg-white border-2 border-slate-200 rounded-xl p-5"
    >
      {/* Header row: style badge + word count */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <div className="flex space-x-2">
          <span className="bg-purple-100 text-purple-700 px-2.5 py-1 rounded-md text-xs font-bold tracking-wider uppercase flex items-center">
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            Style Applied: {tone}
          </span>
        </div>
        <div className="text-xs text-slate-400 font-medium">
          总字数: {charCount} / 预计 {duration}
        </div>
      </div>

      {/* Prose content */}
      <div className="prose prose-slate prose-sm max-w-none text-[15px] space-y-4">
        {paragraphs.map((para, i) => {
          // Last paragraph gets the callout treatment when oral opt is present
          const isCallout = hasOralOpt && i === paragraphs.length - 1;
          return (
            <p
              key={i}
              className={
                isCallout
                  ? 'bg-amber-50 border-l-4 border-amber-400 pl-4 py-1 italic'
                  : ''
              }
            >
              {isCallout && (
                <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded mr-2 align-middle">
                  口语化优化
                </span>
              )}
              {para}
            </p>
          );
        })}
      </div>
    </div>
  );
}
