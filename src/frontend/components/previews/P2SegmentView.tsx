import type { ScriptSegment } from '@frontend/types/preview';
import { CheckCircle2, List } from 'lucide-react';

interface P2SegmentViewProps {
  segments?: ScriptSegment[];
}

function countChineseChars(text: string): number {
  let count = 0;
  for (const ch of text) {
    if (/[一-鿿㐀-䶿]/.test(ch)) {
      count++;
    }
  }
  return count;
}

function estimateDuration(wordCount: number): number {
  // ~4 chars per second for Chinese TTS
  return Math.max(5, Math.round(wordCount / 4));
}

function deriveTitle(segment: ScriptSegment, index: number): string {
  // Use first ~15 chars of content as title if no explicit title
  const firstLine = segment.content.split(/[\n\r]+/)[0] || '';
  if (firstLine.length > 15) return firstLine.slice(0, 15) + '...';
  return firstLine || `段落 ${index + 1}`;
}

function SegmentCard({
  segment,
  index,
}: {
  segment: ScriptSegment;
  index: number;
}) {
  const wordCount = countChineseChars(segment.content);
  const duration = estimateDuration(wordCount);
  const title = deriveTitle(segment, index);
  const hasDataPoints = segment.key_data_points && segment.key_data_points.length > 0;

  return (
    <div className="bg-white border-2 border-slate-200 rounded-xl overflow-hidden shadow-sm relative">
      {hasDataPoints && (
        <div className="absolute top-2.5 right-2 z-10">
          <button className="text-[11px] bg-white text-blue-600 px-2 py-1 rounded-md border border-blue-100 shadow-sm hover:bg-blue-50 font-bold uppercase tracking-wider">
            重写此段
          </button>
        </div>
      )}
      <div className="bg-slate-800 text-white px-4 py-2.5 text-sm font-bold flex justify-between tracking-wide">
        <span>
          段落 {index + 1}: {title}
        </span>
        <span className="text-slate-400 text-xs font-normal">
          约 {wordCount} 字 &bull; {duration} 秒
        </span>
      </div>
      <div className="p-4">
        <p className="text-slate-700 leading-relaxed text-[15px]">
          {segment.content}
        </p>

        {hasDataPoints && (
          <div className="mt-4 pt-4 border-t border-blue-100/50">
            <h4 className="text-[11px] font-bold text-slate-500 mb-2 flex items-center uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4 text-green-500 mr-1.5" />{' '}
              关键数据点核查
            </h4>
            {segment.key_data_points.map((kdp, i) => (
              <div
                key={kdp.data_point_id || i}
                className="bg-white rounded-lg border border-slate-200 p-2.5 text-xs flex justify-between items-center shadow-sm mb-1.5"
              >
                <div>
                  <span className="font-bold text-slate-700">
                    &ldquo;{kdp.label}&rdquo;
                  </span>
                  <span className="text-slate-400 ml-2">{kdp.source}</span>
                </div>
                <span className="text-green-700 bg-green-100 border border-green-200 px-2 py-0.5 rounded-md font-bold text-[10px] tracking-wider uppercase">
                  Verified
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function P2SegmentView({ segments }: P2SegmentViewProps) {
  if (!segments || segments.length === 0) {
    return (
      <div
        data-testid="preview-p2"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <List className="w-12 h-12 mb-3 opacity-40" />
        <p className="text-sm font-medium">暂无分段数据</p>
        <p className="text-xs text-slate-400 mt-1">等待脚本分段 Agent 完成</p>
      </div>
    );
  }

  return (
    <div data-testid="preview-p2" className="space-y-5">
      {segments.map((seg, i) => (
        <SegmentCard key={seg.id} segment={seg} index={i} />
      ))}
    </div>
  );
}
