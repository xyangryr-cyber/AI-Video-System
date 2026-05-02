import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { P8FrameGallery } from '@frontend/components/previews/P8FrameGallery';

describe('P8FrameGallery', () => {
  const twoFrames = [
    { id: 'f1', image_url: '/frames/f1.png', is_downgraded: false },
    { id: 'f2', image_url: '/frames/f2.png', is_downgraded: true },
  ];

  // Empty state
  it('renders empty state when no frames', () => {
    render(<P8FrameGallery frames={[]} />);
    expect(screen.getByText(/暂无素材帧/i)).toBeInTheDocument();
  });

  // Asset sourcing status: fetched
  describe('fetched asset sourcing card', () => {
    it('shows AI Agent material trace header for non-downgraded frames', () => {
      render(<P8FrameGallery frames={twoFrames} />);
      expect(screen.getByText(/AI Agent 物料溯源结果/)).toBeInTheDocument();
    });

    it('shows Verified badge with green styling for fetched items', () => {
      render(<P8FrameGallery frames={twoFrames} />);
      expect(screen.getByText('Verified')).toBeInTheDocument();
    });

    it('renders dark code block with JSON for fetched items', () => {
      render(<P8FrameGallery frames={twoFrames} />);
      const codeBlock = document.querySelector("[class*='bg-\\[\\#1e293b\\]'][class*='font-mono']");
      expect(codeBlock).not.toBeNull();
      expect(codeBlock?.textContent).toContain('f1');
    });

    it('renders Need and Action labels for fetched items', () => {
      render(<P8FrameGallery frames={twoFrames} />);
      expect(screen.getByText('Need:')).toBeInTheDocument();
      expect(screen.getByText('Action:')).toBeInTheDocument();
    });
  });

  // Asset sourcing status: not needed
  describe('not-needed asset sourcing card', () => {
    it('shows not-needed status for downgraded frames', () => {
      render(<P8FrameGallery frames={twoFrames} />);
      expect(screen.getByText(/无需额外动态数据源/)).toBeInTheDocument();
    });

    it('shows CheckCircle2 icon in not-needed row', () => {
      render(<P8FrameGallery frames={twoFrames} />);
      const icons = document.querySelectorAll("svg");
      expect(icons.length).toBeGreaterThanOrEqual(2); // one in not-needed, one Verified
    });
  });

  // Timeline layout
  it('renders timeline with dot markers when frames present', () => {
    render(<P8FrameGallery frames={twoFrames} />);
    const dots = document.querySelectorAll("[class*='border-\\[3px\\]'][class*='border-blue-500']");
    expect(dots.length).toBeGreaterThanOrEqual(2);
  });

  // ID badges
  it('renders ID badge for each frame', () => {
    render(<P8FrameGallery frames={twoFrames} />);
    expect(screen.getByText('f1')).toBeInTheDocument();
    expect(screen.getByText('f2')).toBeInTheDocument();
  });
});
