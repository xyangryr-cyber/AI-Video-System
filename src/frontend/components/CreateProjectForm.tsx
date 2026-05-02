import { useState, FormEvent } from "react"
import type { ReactElement } from "react"

interface Props {
  onSubmit: (input: { title: string; description: string }) => void
  isSubmitting: boolean
  onCancel?: () => void
}

const MIN_DESC = 10

export function CreateProjectForm({ onSubmit, isSubmitting, onCancel }: Props): ReactElement {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState("")
  const [titleTouched, setTitleTouched] = useState(false)

  const isValid = title.trim().length > 0

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setTitleTouched(true)
    if (!title.trim()) {
      setError("标题不能为空")
      return
    }
    if (description.length < MIN_DESC) {
      setError(`描述至少 10 个字`)
      return
    }
    setError("")
    onSubmit({ title, description })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl border-2 border-slate-200 p-8 shadow-sm space-y-6 max-w-xl">
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-2">项目标题</label>
        <input
          id="title" type="text" required
          value={title} onChange={(e) => { setTitle(e.target.value); setTitleTouched(true) }}
          placeholder="例如：2025 Q4 黄金价格走势分析与投资展望"
          className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow"
        />
        {titleTouched && !title.trim() && (
          <p className="text-red-500 text-xs mt-1">标题不能为空</p>
        )}
      </div>
      <div>
        <label htmlFor="desc" className="block text-sm font-medium text-slate-700 mb-2">内容主题描述 (核心观点)</label>
        <textarea
          id="desc" required rows={8}
          value={description} onChange={(e) => setDescription(e.target.value)}
          className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow resize-none"
        />
        <div className="flex justify-between items-center mt-1">
          <span className={`text-xs ${description.length > 0 && description.length < MIN_DESC ? "text-red-500" : "text-slate-400"}`}>
            至少 10 个字符
          </span>
          <span className="text-xs text-slate-400">{description.length} / 2000</span>
        </div>
      </div>
      {error && <div role="alert" className="text-red-600 text-sm">{error}</div>}
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={() => onCancel?.()}
          className="px-6 py-2 text-slate-600 hover:bg-slate-100 rounded-lg font-medium transition-colors"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isSubmitting || !isValid}
          className="px-8 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 transition-colors"
        >
          {isSubmitting ? "创建中..." : "开始制作"}
        </button>
      </div>
    </form>
  )
}
