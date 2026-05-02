import React, { useEffect, useRef } from "react";
import { motion, useSpring, useTransform } from "motion";
import type { TemplateProps } from "@shared/types/template_props";

interface SparklinePoint {
  label: string;
  value: number;
}

interface DataCardData {
  title: string;
  value: number;
  unit: string;
  change: number;
  changeLabel: string;
  sparkline: SparklinePoint[];
}

const DataCard: React.FC<TemplateProps> = ({ data, theme }) => {
  const cardData = data as DataCardData;
  const { color_palette, font_family } = theme;

  const springValue = useSpring(0, { stiffness: 80, damping: 20 });
  const displayValue = useTransform(springValue, (v) => Math.round(v));

  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    springValue.set(cardData.value);
  }, [cardData.value, springValue]);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const points = cardData.sparkline;
    const maxVal = Math.max(...points.map((p) => p.value));
    const minVal = Math.min(...points.map((p) => p.value));
    const range = maxVal - minVal || 1;

    ctx.clearRect(0, 0, w, h);

    ctx.beginPath();
    ctx.strokeStyle = color_palette[0];
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";

    points.forEach((p, i) => {
      const x = (i / (points.length - 1)) * w;
      const y = h - ((p.value - minVal) / range) * (h - 4) - 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, color_palette[0] + "40");
    grad.addColorStop(1, color_palette[0] + "04");
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
  }, [cardData.sparkline, color_palette]);

  const isPositive = cardData.change >= 0;
  const changeColor = isPositive ? color_palette[0] : color_palette[1];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        fontFamily: font_family,
        padding: 20,
        borderRadius: 12,
        backgroundColor: "#ffffff",
        boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
        maxWidth: 320,
      }}
    >
      <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 8, textTransform: "uppercase" }}>
        {cardData.title}
      </div>

      <div style={{ display: "flex", alignItems: "baseline", gap: 4, marginBottom: 4 }}>
        <motion.span style={{ fontSize: 32, fontWeight: 700 }}>
          {displayValue}
        </motion.span>
        <span style={{ fontSize: 14, opacity: 0.5 }}>{cardData.unit}</span>
      </div>

      <div style={{ fontSize: 13, color: changeColor, fontWeight: 600, marginBottom: 12 }}>
        {isPositive ? "+" : ""}{cardData.change} {cardData.changeLabel}
      </div>

      <canvas
        ref={canvasRef}
        width={280}
        height={60}
        style={{ width: "100%", height: 60 }}
      />
    </motion.div>
  );
};

export default DataCard;
