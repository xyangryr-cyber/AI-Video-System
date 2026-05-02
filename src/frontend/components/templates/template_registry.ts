import type { TemplateProps } from "@shared/types/template_props";
import AnimatedLineChart from "./echarts/AnimatedLineChart";
import AnimatedAreaChart from "./echarts/AnimatedAreaChart";
import AnimatedBarChart from "./echarts/AnimatedBarChart";
import AnimatedPieChart from "./echarts/AnimatedPieChart";
import TreemapChart from "./echarts/TreemapChart";
import NumberCallout from "./echarts/NumberCallout";
import CandlestickChart from "./echarts/CandlestickChart";
import ComparisonChart from "./echarts/ComparisonChart";
import NewsCard from "./react/NewsCard";
import QuoteCard from "./react/QuoteCard";
import PolicyComparison from "./react/PolicyComparison";
import EventTimeline from "./react/EventTimeline";
import RelationshipGraph from "./react/RelationshipGraph";
import MapAnnotation from "./react/MapAnnotation";
import DataCard from "./react/DataCard";

export const TEMPLATE_REGISTRY: Record<string, React.FC<TemplateProps>> = {
  animated_line_chart: AnimatedLineChart,
  animated_area_chart: AnimatedAreaChart,
  animated_bar_chart: AnimatedBarChart,
  animated_pie_chart: AnimatedPieChart,
  treemap_chart: TreemapChart,
  number_callout: NumberCallout,
  candlestick_chart: CandlestickChart,
  comparison_chart: ComparisonChart,
  news_card: NewsCard,
  quote_card: QuoteCard,
  policy_comparison: PolicyComparison,
  event_timeline: EventTimeline,
  relationship_graph: RelationshipGraph,
  map_annotation: MapAnnotation,
  data_card: DataCard,
  // P7 storyboard fallback aliases
  chart_card: AnimatedLineChart,
};

/** Maps data_type (from P2 key_data_point) to template_id.
 *  See SPEC-18.3 TEMPLATE_MAPPING table. */
export const TEMPLATE_MAPPING: Record<string, string> = {
  time_series: "animated_line_chart",
  categorical_comparison: "animated_bar_chart",
  proportion: "animated_pie_chart",
  ohlc: "candlestick_chart",
  single_metric: "number_callout",
  trend_with_area: "animated_area_chart",
  multi_series_comparison: "comparison_chart",
  hierarchy: "treemap_chart",
  news_reference: "news_card",
  event_sequence: "event_timeline",
  policy_comparison: "policy_comparison",
  relationship: "relationship_graph",
  person_quote: "quote_card",
  geographic: "map_annotation",
  summary_with_sparkline: "data_card",
};

/**
 * Resolve a template component by data_type.
 * Returns null when data_type has no mapping; caller should invoke LLM recommendation.
 */
export function resolveTemplateByDataType(
  dataType: string
): React.FC<TemplateProps> | null {
  const templateId = TEMPLATE_MAPPING[dataType];
  if (templateId == null) {
    // LLM recommendation is invoked only in this branch by the caller.
    return null;
  }
  return TEMPLATE_REGISTRY[templateId] ?? null;
}

/**
 * Check whether a data_type has a known template mapping.
 */
export function hasTemplateMapping(dataType: string): boolean {
  return dataType in TEMPLATE_MAPPING;
}
