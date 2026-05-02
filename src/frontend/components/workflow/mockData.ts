export interface FactualEntry {
  id: string
  content: string
  usage: string
  source: string
  link: string
  verified: boolean
  method: string
}

export interface WorkflowTask {
  title: string
  completed: boolean
}

export interface ChatMessage {
  role: "agent" | "user"
  text: string
  ts: string
}

export const MOCK_FACTUAL_DATA: FactualEntry[] = [
  {
    id: "F1",
    content: "2025年第一季度全球央行净购金量为290吨",
    usage: "S2E1 / P4 / P6",
    source: "世界黄金协会 (WGC)",
    link: "https://www.gold.org/goldhub/data/gold-demand-trends",
    verified: true,
    method: "官方报告交叉验证",
  },
  {
    id: "F2",
    content: "LBMA 黄金现货价格 2024 年至今上涨约 12.5%",
    usage: "S3E1 / P3",
    source: "LBMA 实时报价接口",
    link: "https://www.lbma.org.uk/prices-and-data",
    verified: true,
    method: "API 通信指纹比对",
  },
  {
    id: "F3",
    content: "美联储 2025 年 3 月放风维持利率不变",
    usage: "P1 / 脚本背景",
    source: "美联储官网新闻稿",
    link: "https://www.federalreserve.gov/newsevents.htm",
    verified: true,
    method: "文本语义一致性确认",
  },
]

export const MOCK_TASKS: WorkflowTask[] = [
  { title: "提取核心信息和视频需求", completed: true },
  { title: "基于需求生成基础大纲", completed: true },
  { title: "大纲细化并拆解为分镜脚本", completed: true },
  { title: "验证数据，修正文本语气", completed: true },
  { title: "向用户报告并发送APP集成清单", completed: true },
]

export const MOCK_MESSAGES: ChatMessage[] = [
  {
    role: "agent",
    text: '我已经根据大纲生成了第 2 版结构化脚本。我注意到您提到了"更口语化一些，不要像背研报"，已经在第二段做了相应调整。',
    ts: "10:24 AM",
  },
  {
    role: "user",
    text: "看起来不错，继续推进吧",
    ts: "10:25 AM",
  },
]

export const MOCK_PROJECT_TITLE = "黄金价格走势分析与投资展望"
export const MOCK_CURRENT_TASK_TITLE = "向用户报告并发送APP集成清单"
