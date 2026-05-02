import React from "react";
import { ComposableMap, Geographies, Geography, Marker, Line, Annotation } from "react-simple-maps";
import { motion } from "motion";
import type { TemplateProps } from "@shared/types/template_props";

interface MapMarker {
  coordinates: [number, number];
  name: string;
  label: string;
  color: string;
}

interface MapLine {
  from: [number, number];
  to: [number, number];
  color: string;
}

interface MapAnnotation {
  coordinates: [number, number];
  text: string;
  dx: number;
  dy: number;
}

interface MapAnnotationData {
  markers: MapMarker[];
  lines: MapLine[];
  annotations: MapAnnotation[];
}

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const MapAnnotationComp: React.FC<TemplateProps> = ({ data, theme }) => {
  const mapData = data as MapAnnotationData;
  const { color_palette, font_family } = theme;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
      style={{ width: "100%", maxWidth: 800, margin: "0 auto", fontFamily: font_family }}
    >
      <ComposableMap projection="geoMercator">
        <Geographies geography={geoUrl}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography key={geo.rsmKey} geography={geo} fill="#EAEAEC" stroke="#D6D6DA" />
            ))
          }
        </Geographies>

        {mapData.markers.map((marker, i) => (
          <motion.g
            key={`marker-${i}`}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: i * 0.2, type: "spring" }}
          >
            <Marker coordinates={marker.coordinates}>
              <circle r={6} fill={marker.color ?? color_palette[0]} stroke="#fff" strokeWidth={2} />
              <text
                textAnchor="middle"
                y={-10}
                style={{ fontSize: 10, fontWeight: 600, fill: marker.color ?? color_palette[0] }}
              >
                {marker.label}
              </text>
            </Marker>
          </motion.g>
        ))}

        {mapData.lines.map((line, i) => (
          <motion.g
            key={`line-${i}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.3 }}
          >
            <Line
              from={line.from}
              to={line.to}
              stroke={line.color ?? color_palette[0]}
              strokeWidth={2}
              strokeLinecap="round"
            />
          </motion.g>
        ))}

        {mapData.annotations.map((ann, i) => (
          <motion.g
            key={`ann-${i}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 + i * 0.2 }}
          >
            <Annotation
              subject={ann.coordinates}
              dx={ann.dx}
              dy={ann.dy}
              connectorProps={{ stroke: color_palette[0], strokeWidth: 1 }}
            >
              <text style={{ fontSize: 10, fill: color_palette[0] }}>{ann.text}</text>
            </Annotation>
          </motion.g>
        ))}
      </ComposableMap>
    </motion.div>
  );
};

export default MapAnnotationComp;
