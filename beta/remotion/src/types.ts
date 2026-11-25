/**
 * types.ts - Core TypeScript Definitions for Remotion Compositions
 */

export interface SceneOnScreen {
  kicker?: string;
  headline: string;
  subheadline?: string;
  data_callout?: string | null;
  status_badge?: string; // 'BREAKING' | 'OFFICIAL' | 'RUMOUR' | 'UPDATE' | 'TACTICAL' | 'EXCLUSIVE'
  source_credit?: string;
}

export interface InfographicData {
  // Transfer Fee Graphic
  transfer_fee?: {
    guaranteed: string;
    add_ons?: string;
    total_package?: string;
    selling_club: string;
    buying_club: string;
    structure?: string;
  };

  // Transfer Route Graphic
  transfer_route?: {
    selling_club: string;
    buying_club: string;
    player_name: string;
    transfer_status: string;
    fee: string;
  };

  // Contract Clause Graphic
  contract_clause?: {
    selling_club: string;
    buying_club: string;
    package_fee: string;
    clause_type: string; // 'BUY-BACK' | 'SELL-ON' | 'RELEASE CLAUSE' | 'APPEARANCE TRIGGER'
    clause_value: string;
    terms?: string;
  };

  // Player Statistics Graphic
  player_statistics?: {
    player_name: string;
    club: string;
    season: string;
    stats: Array<{
      label: string;
      value: string | number;
      highlight?: boolean;
      subtext?: string;
    }>;
  };

  // Tactical Formation Graphic
  tactical_formation?: {
    formation: string; // e.g. "4-3-3", "3-4-2-1", "4-2-3-1"
    team_name: string;
    manager?: string;
    highlight_position: string; // e.g. "CF", "CAM", "DM"
    role_title: string;
    role_description: string;
  };

  // Club Comparison Graphic
  club_comparison?: {
    club_a: { name: string; badge_color?: string };
    club_b: { name: string; badge_color?: string };
    metrics: Array<{
      label: string;
      val_a: string | number;
      val_b: string | number;
    }>;
  };

  // Injury Timeline Graphic
  injury_timeline?: {
    player_name: string;
    club: string;
    diagnosis: string;
    matches_missed: string | number;
    expected_return: string;
    status: "REHABILITATION" | "LIGHT TRAINING" | "FULL TRAINING" | "OUT INDEFINITELY";
    progress_percentage: number;
  };

  // Match Statistics Graphic
  match_statistics?: {
    home_team: string;
    away_team: string;
    home_score: number;
    away_score: number;
    competition: string;
    stats: Array<{
      label: string;
      home_val: string | number;
      away_val: string | number;
    }>;
  };

  // Player Profile Graphic
  player_profile?: {
    player_name: string;
    club: string;
    nationality: string;
    age: number | string;
    position: string;
    market_value: string;
    contract_until: string;
    key_traits?: string[];
  };
}

export interface SceneVisual {
  kind: string;
  primary_subject?: string;
  action_or_context?: string;
  must_explain?: string;
  infographic_data?: InfographicData;
}

export interface SceneMotion {
  type: string; // 'subtle_push_in' | 'slow_pan_right' | 'slow_pan_left' | 'static' | 'wipe_entry'
  direction?: string;
  intensity?: string;
}

export interface SceneTransitionIn {
  id: string;
  duration_sec: number;
  type: string; // 'cross_fade_in' | 'camera_flash' | 'whip_pan' | 'document_snap' | 'shutter_wipe' | 'cross_dissolve'
  sfx_cue?: string | null;
}

export interface SceneShot {
  image_path: string;
  durationInFrames: number;
  focal_x?: number;
  focal_y?: number;
  framing_mode?: "full_bleed" | "broadcast_card" | "pan_horizontal";
  pan_direction?: "left" | "right" | "center";
}

export interface SceneProps {
  scene_id: string;
  role: string;
  narration: string;
  durationInFrames: number;
  audio_path?: string;
  image_path?: string;
  shots?: SceneShot[];
  on_screen: SceneOnScreen;
  visual?: SceneVisual;
  motion?: SceneMotion;
  transition_in?: SceneTransitionIn;
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
  headlinesTabSrc?: string;
  scanlinesSrc?: string;
  enableRetroEffects?: boolean;
  [key: string]: unknown;
}
