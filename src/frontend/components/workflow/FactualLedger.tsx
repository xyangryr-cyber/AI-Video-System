import type { ReactElement } from "react";
import { ExternalLink, ShieldCheck } from "lucide-react";
import type { FactualEntry } from "./mockData";

interface FactualLedgerProps {
  facts: FactualEntry[];
}

export function FactualLedger({ facts }: FactualLedgerProps): ReactElement {
  return (
    <div className="p-5 bg-white border-2 border-slate-200 rounded-2xl flex flex-col flex-[2] min-h-[250px] shadow-sm overflow-hidden">
      <div className="flex justify-between items-center mb-4 shrink-0">
        <h4 className="text-[0.75rem] font-black text-[#1e293b] uppercase tracking-[0.1em] flex items-center">
          <ShieldCheck className="w-3.5 h-3.5 mr-2 text-slate-400" />
          关键事实核实
        </h4>
        <span className="text-[9px] bg-slate-100 text-slate-500 font-bold px-2 py-0.5 rounded-sm uppercase tracking-widest">
          Global Facts
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 pr-1 bg-white border border-slate-200 rounded-xl">
        <ul className="space-y-3" data-testid="fact-list">
          {facts.map((fact) => (
            <li key={fact.id} className="flex gap-3 text-sm text-slate-700 leading-relaxed group">
              <span className="shrink-0 mt-2 w-1.5 h-1.5 rounded-full bg-slate-300 group-hover:bg-blue-400 transition-colors"></span>
              <div className="flex flex-col gap-1.5 w-full">
                <div className="text-[13px] font-medium text-slate-900">{fact.content}</div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                  <span className="font-mono text-slate-400">ID:{fact.id}</span>
                  <a
                    href={fact.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center hover:text-blue-600 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    {fact.source}
                  </a>
                  <span className="flex items-center text-emerald-600">
                    <ShieldCheck className="w-3 h-3 mr-0.5" />
                    已核实
                  </span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
