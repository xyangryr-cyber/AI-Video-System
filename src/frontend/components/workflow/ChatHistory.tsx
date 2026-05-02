import type { ReactElement } from "react"
import type { ChatMessage } from "./mockData"

interface ChatHistoryProps {
  messages: ChatMessage[]
}

export function ChatHistory({ messages }: ChatHistoryProps): ReactElement {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30">
      {messages.map((msg, idx) =>
        msg.role === "agent" ? (
          <div key={idx} className="flex max-w-[90%]">
            <div className="space-y-2">
              <div className="bg-white border-2 border-slate-200/60 rounded-2xl px-5 py-4 text-sm text-slate-700 shadow-sm leading-relaxed">
                <p className="font-medium text-slate-900 mb-1">VideoEngine Agent:</p>
                <p>{msg.text}</p>
              </div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest pl-2">
                {msg.ts}
              </div>
            </div>
          </div>
        ) : (
          <div key={idx} className="flex justify-end">
            <div className="max-w-[85%] flex flex-col items-end gap-2">
              <div className="bg-[#1e293b] rounded-2xl px-5 py-4 text-sm text-white shadow-lg leading-relaxed font-medium">
                {msg.text}
              </div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest pr-2">
                {msg.ts}
              </div>
            </div>
          </div>
        ),
      )}
    </div>
  )
}
