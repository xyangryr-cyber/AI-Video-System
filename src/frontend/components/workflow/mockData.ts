export interface FactualEntry {
  id: string;
  content: string;
  usage: string;
  source: string;
  link: string;
  verified: boolean;
  method: string;
}

export interface WorkflowTask {
  title: string;
  completed: boolean;
}

export interface ChatMessage {
  role: "agent" | "user";
  text: string;
  ts: string;
}

export const MOCK_TASKS: WorkflowTask[] = [
  { title: "提取核心信息和视频需求", completed: true },
  { title: "基于需求生成基础大纲", completed: true },
  { title: "大纲细化并拆解为分镜脚本", completed: true },
  { title: "验证数据，修正文本语气", completed: true },
  { title: "向用户报告并发送APP集成清单", completed: true },
];

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
];

export const MOCK_PROJECT_TITLE = "黄金价格走势分析与投资展望";
export const MOCK_CURRENT_TASK_TITLE = "向用户报告并发送APP集成清单";
