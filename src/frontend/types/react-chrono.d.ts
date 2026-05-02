declare module 'react-chrono' {
  import type { FC } from 'react';

  interface TimelineItem {
    title: string;
    cardTitle: string;
    cardSubtitle: string;
    cardDetailedText?: string;
    media?: {
      name: string;
      source: { url: string };
      type: string;
    };
  }

  interface ChronoTheme {
    primary: string;
    secondary: string;
    cardBgColor: string;
    titleColor: string;
    titleColorActive?: string;
    cardTitleColor?: string;
  }

  interface ChronoProps {
    items: TimelineItem[];
    mode?: 'VERTICAL' | 'VERTICAL_ALTERNATING' | 'HORIZONTAL';
    theme?: ChronoTheme;
    cardHeight?: number;
    slideShow?: boolean;
    slideItemDuration?: number;
    hideControls?: boolean;
    allowDynamicUpdate?: boolean;
    disableClickOnCircle?: boolean;
    [key: string]: unknown;
  }

  export const Chrono: FC<ChronoProps>;
}
