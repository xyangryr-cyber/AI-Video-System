import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PhasePreviewRouter } from '@frontend/components/previews/PhasePreviewRouter';

describe('PhasePreviewRouter', () => {
  // Text visible in each component's empty/placeholder state.
  const phaseIndicator: Record<number, RegExp> = {
    0: /(暂无需求数据|主题)/,
    1: /(暂无脚本内容|段落)/,
    2: /(暂无分段数据|bg-slate-800)/,
    3: /(暂无精修脚本内容|Style Applied)/,
    4: /(暂无音频分段|分段试听)/,
    5: /(暂无 BGM 音频|情感与能量曲线)/,
    6: /^暂无音效数据$/,
    7: /^暂无故事板镜头$/,
    8: /(暂无素材帧|AI Agent 物料溯源)/,
    9: /(暂无关键帧数据|Awaiting P10)/,
    10: /(等待 B-Roll 渲染完成|P10)/,
    11: /视频精剪完成/,
  };

  // AC-1: routes to correct component for each of 12 phases
  describe('AC-1 routes to correct component', () => {
    for (let phase = 0; phase <= 11; phase++) {
      it(`renders phase ${phase} preview`, () => {
        render(<PhasePreviewRouter phase={phase} artifact={{}} />);
        expect(screen.getByTestId(`preview-p${phase}`)).toBeInTheDocument();
        if (phaseIndicator[phase]) {
          expect(screen.getByText(phaseIndicator[phase])).toBeInTheDocument();
        }
      });
    }
  });

  // AC-2: each component accepts and renders SPEC-2.6 props
  describe('AC-2 renders with spec props', () => {
    it('P0 renders requirements', () => {
      render(
        <PhasePreviewRouter
          phase={0}
          artifact={{ requirements: { title: 'Test Project', budget: 5000 } }}
        />
      );
      expect(screen.getByTestId('preview-p0')).toBeInTheDocument();
      expect(screen.getByText(/Test Project/)).toBeInTheDocument();
    });

    it('P1 renders content with version count', () => {
      render(
        <PhasePreviewRouter
          phase={1}
          artifact={{ content: '# Chapter 1\n\nContent here.', versions: 3 }}
        />
      );
      expect(screen.getByTestId('preview-p1')).toBeInTheDocument();
      expect(screen.getByText(/Chapter 1/)).toBeInTheDocument();
      expect(screen.getByText(/3/)).toBeInTheDocument();
    });

    it('P2 renders segment cards with dark header', () => {
      render(
        <PhasePreviewRouter
          phase={2}
          artifact={{
            segments: [
              { id: 'seg-1', content: 'First segment', key_data_points: [{ label: 'Price', value: '$100' }] },
              { id: 'seg-2', content: 'Second segment', key_data_points: [] },
            ],
          }}
        />
      );
      expect(screen.getByTestId('preview-p2')).toBeInTheDocument();
      // Dark header card shows "段落 1:" and content text
      expect(screen.getByText(/段落 1/)).toBeInTheDocument();
      expect(screen.getAllByText(/First segment/).length).toBeGreaterThanOrEqual(1);
    });

    it('P3 renders voice script with directions', () => {
      render(
        <PhasePreviewRouter
          phase={3}
          artifact={{
            content: 'Voice script content',
            voice_directions: [{ text: 'slow', tone: 'serious' }, { text: 'fast', pace: 'quick' }],
          }}
        />
      );
      expect(screen.getByTestId('preview-p3')).toBeInTheDocument();
      expect(screen.getByText(/Voice script content/)).toBeInTheDocument();
    });

    it('P4 renders audio segment rows with play buttons', () => {
      render(
        <PhasePreviewRouter
          phase={4}
          artifact={{
            segments: [
              { id: 's1', audio_url: '/audio/s1.mp3', text: 'Hello', duration_sec: 2.5 },
              { id: 's2', audio_url: '/audio/s2.mp3', text: 'World', duration_sec: 3.0 },
            ],
          }}
        />
      );
      expect(screen.getByTestId('preview-p4')).toBeInTheDocument();
      // New P4 renders segment IDs in labels, not the text field
      expect(screen.getByText(/段落.*s1.*音频/)).toBeInTheDocument();
      expect(screen.getByText(/段落.*s2.*音频/)).toBeInTheDocument();
    });

    it('P5 renders mood curve and BGM track', () => {
      render(
        <PhasePreviewRouter
          phase={5}
          artifact={{ audio_url: '/audio/narration.mp3', duration_sec: 120 }}
        />
      );
      expect(screen.getByTestId('preview-p5')).toBeInTheDocument();
      // New P5 shows mood curve section label
      expect(screen.getByText(/情感与能量曲线/)).toBeInTheDocument();
    });

    it('P6 renders sfx trigger list', () => {
      render(
        <PhasePreviewRouter
          phase={6}
          artifact={{
            sfx_list: [
              { type: 'whoosh', time_sec: 5.0, audio_url: '/sfx/whoosh.mp3' },
              { type: 'ding', time_sec: 10.0, audio_url: '/sfx/ding.mp3' },
            ],
          }}
        />
      );
      expect(screen.getByTestId('preview-p6')).toBeInTheDocument();
      expect(screen.getAllByText(/whoosh/).length).toBeGreaterThanOrEqual(1);
    });

    it('P7 renders storyboard shot cards', () => {
      render(
        <PhasePreviewRouter
          phase={7}
          artifact={{
            shots: [
              { id: 'shot-1', description: 'Opening scene', duration_sec: 5, template_id: 'tpl-1' },
              { id: 'shot-2', description: 'Main content', duration_sec: 10, template_id: 'tpl-2' },
            ],
          }}
        />
      );
      expect(screen.getByTestId('preview-p7')).toBeInTheDocument();
      expect(screen.getAllByText(/Opening scene/).length).toBeGreaterThanOrEqual(1);
    });

    it('P8 renders frame grid', () => {
      render(
        <PhasePreviewRouter
          phase={8}
          artifact={{
            frames: [
              { id: 'f1', image_url: '/frames/f1.png', is_downgraded: false },
              { id: 'f2', image_url: '/frames/f2.png', is_downgraded: true },
            ],
          }}
        />
      );
      expect(screen.getByTestId('preview-p8')).toBeInTheDocument();
      // downgraded frame shows not-needed asset status
      expect(screen.getByText(/无需额外动态数据源/)).toBeInTheDocument();
    });

    it('P9 renders broll timeline cards', () => {
      render(
        <PhasePreviewRouter
          phase={9}
          artifact={{
            brolls: [
              { id: 'b1', thumbnail_url: '/broll/b1.jpg', source: 'stock', is_placeholder: false },
              { id: 'b2', thumbnail_url: '/broll/b2.jpg', source: 'generated', is_placeholder: true },
            ],
          }}
        />
      );
      expect(screen.getByTestId('preview-p9')).toBeInTheDocument();
      // New P9 shows render status badges; placeholder items show "Awaiting P10"
      expect(screen.getByText(/Awaiting P10/)).toBeInTheDocument();
    });

    it('P10 renders video player', () => {
      render(
        <PhasePreviewRouter
          phase={10}
          artifact={{
            video_url: '/video/final.mp4',
            duration_sec: 180,
            subtitles_url: '/video/final.srt',
          }}
        />
      );
      expect(screen.getByTestId('preview-p10')).toBeInTheDocument();
      expect(screen.getByText(/180/)).toBeInTheDocument();
    });

    it('P11 renders final player with covers and download', () => {
      render(
        <PhasePreviewRouter
          phase={11}
          artifact={{
            video_url: '/video/final.mp4',
            covers: [
              { url: '/covers/cover1.jpg', aspect_ratio: '16:9' },
              { url: '/covers/cover2.jpg', aspect_ratio: '1:1' },
            ],
            download_urls: { '1080p': '/dl/1080p.mp4', '720p': '/dl/720p.mp4' },
          }}
        />
      );
      expect(screen.getByTestId('preview-p11')).toBeInTheDocument();
      expect(screen.getByText(/Download/)).toBeInTheDocument();
    });
  });

  // AC-6: empty/missing data handled gracefully
  describe('AC-6 empty data graceful', () => {
    it('does not crash with undefined artifact', () => {
      render(<PhasePreviewRouter phase={0} />);
      expect(screen.getByTestId('preview-p0')).toBeInTheDocument();
    });

    it('does not crash with null artifact', () => {
      render(<PhasePreviewRouter phase={4} artifact={null as unknown} />);
      expect(screen.getByTestId('preview-p4')).toBeInTheDocument();
    });

    it('does not crash with empty object artifact', () => {
      render(<PhasePreviewRouter phase={8} artifact={{}} />);
      expect(screen.getByTestId('preview-p8')).toBeInTheDocument();
    });

    it('renders unknown phase gracefully', () => {
      render(<PhasePreviewRouter phase={99} />);
      expect(screen.getByTestId('preview-empty')).toBeInTheDocument();
      expect(screen.getByText(/not supported/i)).toBeInTheDocument();
    });
  });
});
