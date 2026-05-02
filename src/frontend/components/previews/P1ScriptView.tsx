import { FileText } from 'lucide-react';

interface P1ScriptViewProps {
  content?: string;
  versions?: number;
}

interface OutlineSection {
  title: string;
  desc: string;
}

function parseOutlineSections(content: string): OutlineSection[] {
  const lines = content.split('\n');
  const sections: OutlineSection[] = [];
  let currentTitle = '';
  let currentLines: string[] = [];

  for (const line of lines) {
    const headingMatch = line.match(/^#{1,3}\s+(.+)/);
    if (headingMatch) {
      if (currentTitle || currentLines.length > 0) {
        sections.push({
          title: currentTitle || '未命名段落',
          desc: currentLines.join('\n').trim() || currentTitle,
        });
      }
      currentTitle = headingMatch[1].trim();
      currentLines = [];
    } else {
      currentLines.push(line);
    }
  }

  // Flush last section
  if (currentTitle || currentLines.length > 0) {
    sections.push({
      title: currentTitle || '未命名段落',
      desc: currentLines.join('\n').trim() || currentTitle,
    });
  }

  return sections;
}

export function P1ScriptView({ content, versions }: P1ScriptViewProps) {
  if (!content || content.trim() === '') {
    return (
      <div
        data-testid="preview-p1"
        className="flex flex-col items-center justify-center h-64 text-slate-400"
      >
        <FileText className="w-12 h-12 mb-3 opacity-40" />
        <p className="text-sm font-medium">暂无脚本内容</p>
        <p className="text-xs text-slate-400 mt-1">等待脚本生成 Agent 完成</p>
      </div>
    );
  }

  const sections = parseOutlineSections(content);

  return (
    <div data-testid="preview-p1" className="space-y-4">
      {versions !== undefined && (
        <div className="flex justify-end">
          <span className="bg-purple-100 text-purple-700 px-2.5 py-1 rounded-md text-xs font-bold">
            v{versions}
          </span>
        </div>
      )}
      {sections.map((item, i) => (
        <div
          key={i}
          className="flex gap-4 items-start bg-white border-2 border-slate-200 rounded-xl p-4 shadow-sm relative overflow-hidden"
        >
          <div className="w-1 absolute left-0 top-0 bottom-0 bg-blue-500"></div>
          <div className="w-8 h-8 shrink-0 bg-blue-50 text-blue-600 font-bold rounded-lg flex items-center justify-center text-sm border border-blue-100">
            {i + 1}
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-sm mb-1">{item.title}</h3>
            <p className="text-sm text-slate-600">{item.desc}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
