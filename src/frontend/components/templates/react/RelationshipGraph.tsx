import React from "react";
import { ResponsiveNetwork } from "@nivo/network";
import { motion } from "motion";
import type { TemplateProps } from "@shared/types/template_props";

interface GraphNode {
  id: string;
  name: string;
  group: string;
  radius?: number;
  color?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

interface RelationshipGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const RelationshipGraph: React.FC<TemplateProps> = ({ data, theme }) => {
  const graphData = data as RelationshipGraphData;
  const { color_palette, font_family } = theme;

  const nodeMap = new Map(graphData.nodes.map((n) => [n.id, n]));

  const nivoData = {
    nodes: graphData.nodes.map((n) => ({ id: n.id })),
    links: graphData.edges.map((e) => ({
      source: e.source,
      target: e.target,
    })),
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{ width: "100%", height: 400, fontFamily: font_family }}
    >
      <svg width="100%" height="100%" viewBox="0 0 800 400">
        <defs>
          {graphData.edges.map((_, i) => (
            <motion.path
              key={i}
              id={`edge-${i}`}
              stroke={color_palette[0]}
              strokeWidth={2}
              fill="none"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1.5, delay: i * 0.2 }}
              d={`M${i * 100 + 50},200 Q${i * 100 + 100},100 ${i * 100 + 150},200`}
            />
          ))}
        </defs>
      </svg>
      <ResponsiveNetwork
        data={nivoData}
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        linkDistance={80}
        centeringStrength={0.3}
        repulsivity={6}
        nodeSize={(n) => nodeMap.get(n.id)?.radius ?? 12}
        nodeColor={(n) => nodeMap.get(n.id)?.color ?? color_palette[0]}
        nodeBorderWidth={2}
        nodeBorderColor={{ from: "color", modifiers: [["darker", 0.8]] }}
        linkThickness={2}
        linkColor={{ from: "source.color" }}
        motionConfig="gentle"
      />
    </motion.div>
  );
};

export default RelationshipGraph;
