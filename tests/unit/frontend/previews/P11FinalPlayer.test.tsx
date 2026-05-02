import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { P11FinalPlayer } from '@frontend/components/previews/P11FinalPlayer';

describe('P11FinalPlayer', () => {
  const artifact = {
    video_url: '/video/final.mp4',
    covers: [
      { url: '/covers/cover1.jpg', aspect_ratio: '16:9' },
      { url: '/covers/cover2.jpg', aspect_ratio: '1:1' },
    ],
    download_urls: { '1080p': '/dl/1080p.mp4', '720p': '/dl/720p.mp4' },
  };

  it('renders completion checkmark section', () => {
    render(<P11FinalPlayer {...artifact} />);
    expect(screen.getByText('视频精剪完成!')).toBeInTheDocument();
  });

  it('renders embedded video player when video_url provided', () => {
    render(<P11FinalPlayer {...artifact} />);
    const video = screen.getByTestId('final-video-player');
    expect(video).toBeInTheDocument();
    expect(video.tagName).toBe('VIDEO');
  });

  it('shows no-video placeholder when video_url absent', () => {
    render(<P11FinalPlayer covers={artifact.covers} />);
    expect(screen.getByText('无视频数据')).toBeInTheDocument();
  });

  it('renders cover images when covers provided', () => {
    render(<P11FinalPlayer {...artifact} />);
    const coverImages = screen.getAllByAltText(/cover/i);
    expect(coverImages).toHaveLength(2);
  });

  it('shows aspect ratio for each cover', () => {
    render(<P11FinalPlayer {...artifact} />);
    expect(screen.getByText(/16:9/)).toBeInTheDocument();
    expect(screen.getByText(/1:1/)).toBeInTheDocument();
  });

  it('renders platform download cards', () => {
    render(<P11FinalPlayer {...artifact} />);
    expect(screen.getByText(/下载 B 站版本/)).toBeInTheDocument();
    expect(screen.getByText(/下载抖音版本/)).toBeInTheDocument();
  });

  it('renders SRT subtitle row', () => {
    render(<P11FinalPlayer {...artifact} />);
    expect(screen.getByText(/配套字幕文件/)).toBeInTheDocument();
  });

  it('platform download cards render without download_urls', () => {
    render(<P11FinalPlayer video_url="/video/final.mp4" />);
    expect(screen.getByText(/下载 B 站版本/)).toBeInTheDocument();
    expect(screen.getByText(/下载抖音版本/)).toBeInTheDocument();
  });
});
