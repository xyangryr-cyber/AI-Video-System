declare module 'react-simple-maps' {
  import type { FC, ReactNode } from 'react';

  interface GeographyProps {
    geography: Record<string, unknown>;
    fill?: string;
    stroke?: string;
    strokeWidth?: number;
    style?: Record<string, unknown>;
    className?: string;
  }

  interface MarkerProps {
    coordinates: [number, number];
    children?: ReactNode;
    className?: string;
  }

  interface LineProps {
    from: [number, number];
    to: [number, number];
    stroke?: string;
    strokeWidth?: number;
    strokeLinecap?: string;
    className?: string;
  }

  interface AnnotationProps {
    subject: [number, number];
    dx: number;
    dy: number;
    connectorProps?: Record<string, unknown>;
    children?: ReactNode;
    className?: string;
  }

  export const ComposableMap: FC<{
    projection?: string;
    projectionConfig?: Record<string, unknown>;
    width?: number;
    height?: number;
    style?: Record<string, unknown>;
    children?: ReactNode;
    [key: string]: unknown;
  }>;

  export const Geographies: FC<{
    geography: string | Record<string, unknown>;
    children: (data: { geographies: Array<{ rsmKey: string; properties: Record<string, unknown> }> }) => ReactNode;
    [key: string]: unknown;
  }>;

  export const Geography: FC<GeographyProps>;
  export const Marker: FC<MarkerProps>;
  export const Line: FC<LineProps>;
  export const Annotation: FC<AnnotationProps>;
  export const ZoomableGroup: FC<{ children?: ReactNode; [key: string]: unknown }>;
}
