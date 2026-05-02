import React from "react";
import { motion } from "motion";
import Lottie from "lottie-react";
import type { TemplateProps } from "@shared/types/template_props";

interface NewsItem {
  headline: string;
  lines: string[];
  sentiment: "positive" | "negative" | "neutral";
}

interface NewsCardData {
  items: NewsItem[];
}

const sentimentAnimations: Record<string, unknown> = {
  positive: {},
  negative: {},
  neutral: {},
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, x: -60 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.5, ease: [0, 0, 0.2, 1] as const },
  },
};

const NewsCard: React.FC<TemplateProps> = ({ data, theme }) => {
  const newsData = data as NewsCardData;
  const { color_palette, font_family } = theme;

  return (
    <motion.div
      style={{ fontFamily: font_family }}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {newsData.items.map((item, i) => (
        <motion.div
          key={i}
          variants={itemVariants}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 16,
            padding: 12,
            borderRadius: 8,
            backgroundColor: color_palette[i % color_palette.length] + "18",
          }}
        >
          <Lottie
            animationData={sentimentAnimations[item.sentiment]}
            style={{ width: 32, height: 32 }}
            loop={false}
          />
          <div>
            <div style={{ fontWeight: 700, marginBottom: 4 }}>{item.headline}</div>
            {item.lines.map((line, j) => (
              <motion.div key={j} variants={itemVariants} style={{ fontSize: 14, opacity: 0.85 }}>
                {line}
              </motion.div>
            ))}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
};

export default NewsCard;
