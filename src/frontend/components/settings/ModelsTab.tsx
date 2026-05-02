import type { ReactElement } from "react";
import { useState } from "react";
import { Save } from "lucide-react";

export function ModelsTab(): ReactElement {
  const [temperature, setTemperature] = useState(0.7);
  const [maxAttempts, setMaxAttempts] = useState(3);
  const [reviewModel, setReviewModel] = useState("gemini-2.0-flash");
  const [concurrency, setConcurrency] = useState("serial");

  return (
    <div
      data-testid="models-tab"
      className="bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col"
    >
      <div className="p-6 border-b border-slate-200 shrink-0">
        <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">
          模型与策略配置
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          全局模型的生成控制、失败重试等任务编排调度策略。
        </p>
      </div>
      <div className="p-6 space-y-6 overflow-y-auto">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div className="col-span-2 sm:col-span-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              生成模型温度 (Temperature)
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-[11px] text-slate-400 mt-2">
              <span>0.0 (更稳定)</span>
              <span className="text-slate-600 font-medium bg-slate-100 px-2 py-0.5 rounded">
                当前: {temperature.toFixed(1)}
              </span>
              <span>1.0 (更有创意)</span>
            </div>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              任务失败最大重试次数 (max_attempts)
            </label>
            <input
              type="number"
              value={maxAttempts}
              onChange={(e) =>
                setMaxAttempts(Math.max(1, Math.min(5, parseInt(e.target.value) || 1)))
              }
              min={1}
              max={5}
              className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
            />
          </div>
          <div className="col-span-2">
            <div className="border-t border-slate-100 my-2"></div>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              审核模型 (Reviewer Agents)
            </label>
            <select
              value={reviewModel}
              onChange={(e) => setReviewModel(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
            >
              <option>gemini-2.0-flash</option>
              <option>gemini-2.0-pro-exp-02-05</option>
            </select>
            <p className="text-xs text-slate-500 mt-1">负责通过各阶段门禁检查</p>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              异步任务并发策略
            </label>
            <select
              value={concurrency}
              onChange={(e) => setConcurrency(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
            >
              <option value="serial">单线程串行 (V1 默认)</option>
              <option value="pool" disabled>
                多线程池 (V1.5+ 支持)
              </option>
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
  );
}
