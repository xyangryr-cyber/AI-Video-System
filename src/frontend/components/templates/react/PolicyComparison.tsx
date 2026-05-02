import React from "react";
import { motion, AnimatePresence } from "motion";
import type { TemplateProps } from "@shared/types/template_props";

interface PolicyRow {
  id: string;
  indicator: string;
  before: string;
  after: string;
  change: string;
  highlighted?: boolean;
}

interface PolicyComparisonData {
  title: string;
  rows: PolicyRow[];
}

const rowVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { layout: { duration: 0.3 } },
  },
  exit: { opacity: 0, scale: 0.95 },
};

const PolicyComparison: React.FC<TemplateProps> = ({ data, theme }) => {
  const policyData = data as PolicyComparisonData;
  const { color_palette, font_family } = theme;

  return (
    <div style={{ fontFamily: font_family, padding: 24 }}>
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ textAlign: "center", marginBottom: 24, fontSize: 22 }}
      >
        {policyData.title}
      </motion.h2>

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={thStyle}>Indicator</th>
            <th style={thStyle}>Before</th>
            <th style={thStyle}>After</th>
            <th style={thStyle}>Change</th>
          </tr>
        </thead>
        <tbody>
          <AnimatePresence>
            {policyData.rows.map((row) => (
              <motion.tr
                key={row.id}
                variants={rowVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                layout
                style={{
                  backgroundColor: row.highlighted ? color_palette[0] + "22" : "transparent",
                }}
                whileHover={{ scale: 1.02 }}
              >
                <td style={tdStyle}>{row.indicator}</td>
                <td style={tdStyle}>{row.before}</td>
                <td style={tdStyle}>{row.after}</td>
                <td
                  style={{
                    ...tdStyle,
                    color: row.change.startsWith("+") ? color_palette[0] : color_palette[1],
                    fontWeight: 700,
                  }}
                >
                  {row.change}
                </td>
              </motion.tr>
            ))}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 14px",
  borderBottom: "2px solid #e0e0e0",
  fontSize: 14,
  fontWeight: 600,
  opacity: 0.7,
};

const tdStyle: React.CSSProperties = {
  padding: "10px 14px",
  borderBottom: "1px solid #f0f0f0",
  fontSize: 14,
};

export default PolicyComparison;
