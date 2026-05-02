import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { P4SegmentAudioPlayer } from '@frontend/components/previews/P4SegmentAudioPlayer';

describe('P4SegmentAudioPlayer', () => {
  const twoSegments = [
    { id: 'seg-1', audio_url: '/audio/seg1.mp3', text: 'First segment narration', duration_sec: 3.5 },
    { id: 'seg-2', audio_url: '/audio/seg2.mp3', text: 'Second segment narration', duration_sec: 4.0 },
  ];

  // AC-3: per-segment play/pause controls
  describe('AC-3 per-segment play/pause', () => {
    it('renders a play button for each segment', () => {
      render(<P4SegmentAudioPlayer segments={twoSegments} />);
      const playButtons = screen.getAllByRole('button', { name: /^play segment/i });
      expect(playButtons).toHaveLength(2);
    });

    it('play button is present per segment even with single segment', () => {
      render(<P4SegmentAudioPlayer segments={[twoSegments[0]]} />);
      expect(screen.getByRole('button', { name: /^play segment/i })).toBeInTheDocument();
    });

    it('play button text shows per-segment label', () => {
      render(<P4SegmentAudioPlayer segments={twoSegments} />);
      expect(screen.getByRole('button', { name: /play segment seg-1/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /play segment seg-2/i })).toBeInTheDocument();
    });

    it('clicking play toggles to pause button text', async () => {
      render(<P4SegmentAudioPlayer segments={twoSegments} />);
      const playBtn = screen.getByRole('button', { name: /play segment seg-1/i });
      await userEvent.click(playBtn);
      expect(screen.getByRole('button', { name: /pause segment seg-1/i })).toBeInTheDocument();
    });

    it('clicking pause toggles back to play button text', async () => {
      render(<P4SegmentAudioPlayer segments={twoSegments} />);
      const playBtn = screen.getByRole('button', { name: /play segment seg-1/i });
      await userEvent.click(playBtn); // play -> pause
      const pauseBtn = screen.getByRole('button', { name: /pause segment seg-1/i });
      await userEvent.click(pauseBtn); // pause -> play
      expect(screen.getByRole('button', { name: /play segment seg-1/i })).toBeInTheDocument();
    });

    it('playing one segment does not affect another segment button', async () => {
      render(<P4SegmentAudioPlayer segments={twoSegments} />);
      await userEvent.click(screen.getByRole('button', { name: /play segment seg-1/i }));
      // seg-1 should now show pause, seg-2 should still show play
      expect(screen.getByRole('button', { name: /pause segment seg-1/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /play segment seg-2/i })).toBeInTheDocument();
    });
  });

  // Empty state
  it('renders empty state when no segments', () => {
    render(<P4SegmentAudioPlayer segments={[]} />);
    expect(screen.getByText(/暂无音频分段/i)).toBeInTheDocument();
  });

  it('renders segment label and duration for each segment', () => {
    render(<P4SegmentAudioPlayer segments={twoSegments} />);
    expect(screen.getByText(/段落.*seg-1.*音频/)).toBeInTheDocument();
    expect(screen.getByText(/0:3\.5/)).toBeInTheDocument();
    expect(screen.getByText(/段落.*seg-2.*音频/)).toBeInTheDocument();
    expect(screen.getByText(/0:04/)).toBeInTheDocument();
  });
});
