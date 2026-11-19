export interface SceneOnScreen {
  kicker?: string;
  headline: string;
  subheadline?: string;
  data_callout?: string | null;
  status_badge?: string;
}

export interface SceneVisual {
  kind: string;
  primary_subject?: string;
  action_or_context?: string;
  must_explain?: string;
}

export interface SceneMotion {
  type: string;
  direction?: string;
  intensity?: string;
}

export interface SceneProps {
  scene_id: string;
  role: string;
  narration: string;
  durationInFrames: number;
  audio_path?: string;
  image_path?: string;
  on_screen: SceneOnScreen;
  visual?: SceneVisual;
  motion?: SceneMotion;
}

export interface SubtitleCue {
  id: number;
  start_frame: number;
  end_frame: number;
  text: string;
}

export interface FootballShortProps {
  story_id: string;
  headline: string;
  totalDurationInFrames: number;
  scenes: SceneProps[];
  tickerText: string;
  subtitles: SubtitleCue[];
  kicker: string;
  logoSrc?: string;
  masterLogoSrc?: string;
  tickerBaseSrc?: string;
  scanlinesSrc?: string;
  enableRetroEffects?: boolean;
}
