import React from "react";
import { Chrono } from "react-chrono";
import { motion } from "motion";
import type { TemplateProps } from "@shared/types/template_props";
import { resolveChartData, validateChartMaterial } from "@frontend/render/chart_material_priority";

interface TimelineEvent {
  title: string;
  cardTitle: string;
  cardSubtitle: string;
  cardDetailedText: string;
}

interface EventTimelineData {
  events: TimelineEvent[];
}

const EventTimeline: React.FC<TemplateProps> = (props) => {
  const { theme } = props;

  validateChartMaterial(props);
  const resolved = resolveChartData(props);

  const color_palette = theme.color_palette;
  const font_family = theme.font_family;

  let events: TimelineEvent[] = [];

  if (resolved.source === "chart_material" && Array.isArray(resolved.data)) {
    // chart_material for event_timeline: series is [{ name, data: [...] }]
    // where data contains event objects
    const seriesArr = resolved.data as { name: string; data: unknown[] }[];
    for (const s of seriesArr) {
      for (const item of s.data) {
        if (item && typeof item === "object") {
          const ev = item as Record<string, unknown>;
          events.push({
            title: (ev.title as string) ?? "",
            cardTitle: (ev.cardTitle as string) ?? (ev.title as string) ?? "",
            cardSubtitle: (ev.cardSubtitle as string) ?? "",
            cardDetailedText: (ev.cardDetailedText as string) ?? "",
          });
        }
      }
    }
  } else {
    const timelineData = resolved.data as EventTimelineData;
    events = timelineData.events ?? [];
  }

  const items = events.map((e) => ({
    title: e.title,
    cardTitle: e.cardTitle,
    cardSubtitle: e.cardSubtitle,
    cardDetailedText: e.cardDetailedText,
  }));

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-100px" }}
      style={{ fontFamily: font_family, padding: 24 }}
    >
      <Chrono
        items={items}
        mode="VERTICAL_ALTERNATING"
        theme={{
          primary: color_palette[0],
          secondary: color_palette[1],
          cardBgColor: "#ffffff",
          titleColor: color_palette[0],
        }}
      />
    </motion.div>
  );
};

export default EventTimeline;
