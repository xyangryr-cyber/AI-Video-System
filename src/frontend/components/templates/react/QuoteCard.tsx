import React from "react";
import { motion } from "motion";
import Lottie from "lottie-react";
import type { TemplateProps } from "@shared/types/template_props";

interface QuoteCardData {
  quote: string;
  author: string;
  source: string;
}

const quotationMarkAnimation = {};

const wordVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.3 },
  }),
};

const QuoteCard: React.FC<TemplateProps> = ({ data, theme }) => {
  const quoteData = data as QuoteCardData;
  const words = quoteData.quote.split(/\s+/);
  const { font_family } = theme;

  return (
    <div style={{ fontFamily: font_family, padding: 24 }}>
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}
      >
        <Lottie
          animationData={quotationMarkAnimation}
          style={{ width: 48, height: 48 }}
          loop={false}
        />
      </motion.div>

      <div
        style={{
          fontSize: 24,
          lineHeight: 1.6,
          fontStyle: "italic",
          textAlign: "center",
          maxWidth: 700,
          margin: "0 auto",
        }}
      >
        {words.map((word, i) => (
          <motion.span
            key={i}
            custom={i}
            variants={wordVariants}
            initial="hidden"
            animate="visible"
            style={{ display: "inline-block", marginRight: 6 }}
          >
            {word}
          </motion.span>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: words.length * 0.08 + 0.4 }}
        style={{ textAlign: "center", marginTop: 20, opacity: 0.7 }}
      >
        — {quoteData.author}, {quoteData.source}
      </motion.div>
    </div>
  );
};

export default QuoteCard;
