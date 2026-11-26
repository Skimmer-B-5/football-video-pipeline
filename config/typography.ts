/**
 * config/typography.ts
 * 
 * 30 Football Plus — Permanent Central Typography Design System
 * Defines the single source of truth for all video text, subtitles, graphics,
 * lower-thirds, data cards, outro branding, and Telegram scene charts.
 * 
 * Three Approved Font Families:
 * 1. Barlow Condensed — Primary display & headlines (SemiBold 600, Bold 700, ExtraBold 800, Black 900)
 * 2. Inter — Reading, subtitles & supporting copy (Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800)
 * 3. IBM Plex Mono — Structured data, kickers, timestamps & technical labels (Medium 500, SemiBold 600)
 */

export interface FontDefinition {
  family: string;
  weight: number | string;
  localFile: string;
}

export interface TypographyToken {
  fontFamily: string;
  fontWeight: number;
  fontSize: number;
  lineHeight: number;
  letterSpacing?: number;
  textTransform?: 'uppercase' | 'none' | 'capitalize';
  maxLines?: number;
  maxCharsPerLine?: number;
  color: string;
  shadow?: string;
  description: string;
}

export interface TypographySafeZones {
  canvasWidth: number;
  canvasHeight: number;
  marginHorizontalMin: number;
  marginHorizontalPreferred: number;
  brandIdentifierY: [number, number];
  primaryHeadlineY: [number, number];
  supportingInfoY: [number, number];
  subtitleY: [number, number];
  avoidBelowY: number;
}

export const FONT_FAMILIES = {
  DISPLAY: 'Barlow Condensed',
  READING: 'Inter',
  MONO: 'IBM Plex Mono',
} as const;

export const LOCAL_FONT_FILES: Record<string, FontDefinition> = {
  // Barlow Condensed
  'BarlowCondensed-SemiBold': {
    family: FONT_FAMILIES.DISPLAY,
    weight: 600,
    localFile: 'barlow_condensed/BarlowCondensed-SemiBold.ttf',
  },
  'BarlowCondensed-Bold': {
    family: FONT_FAMILIES.DISPLAY,
    weight: 700,
    localFile: 'barlow_condensed/BarlowCondensed-Bold.ttf',
  },
  'BarlowCondensed-ExtraBold': {
    family: FONT_FAMILIES.DISPLAY,
    weight: 800,
    localFile: 'barlow_condensed/BarlowCondensed-ExtraBold.ttf',
  },
  'BarlowCondensed-Black': {
    family: FONT_FAMILIES.DISPLAY,
    weight: 900,
    localFile: 'barlow_condensed/BarlowCondensed-Black.ttf',
  },

  // Inter
  'Inter-Regular': {
    family: FONT_FAMILIES.READING,
    weight: 400,
    localFile: 'inter/Inter-Regular.ttf',
  },
  'Inter-Medium': {
    family: FONT_FAMILIES.READING,
    weight: 500,
    localFile: 'inter/Inter-Medium.ttf',
  },
  'Inter-SemiBold': {
    family: FONT_FAMILIES.READING,
    weight: 600,
    localFile: 'inter/Inter-SemiBold.ttf',
  },
  'Inter-Bold': {
    family: FONT_FAMILIES.READING,
    weight: 700,
    localFile: 'inter/Inter-Bold.ttf',
  },
  'Inter-ExtraBold': {
    family: FONT_FAMILIES.READING,
    weight: 800,
    localFile: 'inter/Inter-ExtraBold.ttf',
  },

  // IBM Plex Mono
  'IBMPlexMono-Medium': {
    family: FONT_FAMILIES.MONO,
    weight: 500,
    localFile: 'ibm_plex_mono/IBMPlexMono-Medium.ttf',
  },
  'IBMPlexMono-SemiBold': {
    family: FONT_FAMILIES.MONO,
    weight: 600,
    localFile: 'ibm_plex_mono/IBMPlexMono-SemiBold.ttf',
  },
};

export const SAFE_ZONES: TypographySafeZones = {
  canvasWidth: 1080,
  canvasHeight: 1920,
  marginHorizontalMin: 72,
  marginHorizontalPreferred: 84,
  brandIdentifierY: [100, 180],
  primaryHeadlineY: [240, 580],
  supportingInfoY: [1080, 1320],
  subtitleY: [1390, 1600],
  avoidBelowY: 1640,
};

export const TYPOGRAPHY_TOKENS: Record<string, TypographyToken> = {
  brandMark: {
    fontFamily: FONT_FAMILIES.DISPLAY,
    fontWeight: 700,
    fontSize: 62,
    lineHeight: 1.0,
    textTransform: 'uppercase',
    color: '#FFFFFF',
    description: '30 Football Plus primary broadcast wordmark',
  },

  breakingKicker: {
    fontFamily: FONT_FAMILIES.MONO,
    fontWeight: 600,
    fontSize: 24,
    lineHeight: 1.15,
    letterSpacing: 1.4,
    textTransform: 'uppercase',
    color: '#FACC15', // Vibrant yellow
    description: 'Breaking news status kicker capsule (e.g. BREAKING NEWS, VERIFIED)',
  },

  categoryLabel: {
    fontFamily: FONT_FAMILIES.MONO,
    fontWeight: 600,
    fontSize: 24,
    lineHeight: 1.15,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    color: '#38BDF8', // Cyan accent
    description: 'Story category pill (e.g. TRANSFER WATCH, TEAM NEWS)',
  },

  primaryHeadline: {
    fontFamily: FONT_FAMILIES.DISPLAY,
    fontWeight: 800,
    fontSize: 78, // Scale range 72–84px, long titles drop to 64–70px
    lineHeight: 0.98,
    maxLines: 2,
    textTransform: 'uppercase',
    color: '#FFFFFF',
    shadow: '0 4px 16px rgba(0,0,0,0.7)',
    description: 'Main news headline for vertical 9:16 canvas',
  },

  primaryHeadlineCompact: {
    fontFamily: FONT_FAMILIES.DISPLAY,
    fontWeight: 800,
    fontSize: 66,
    lineHeight: 0.98,
    maxLines: 2,
    textTransform: 'uppercase',
    color: '#FFFFFF',
    description: 'Condensed main headline for longer phrases (>35 characters)',
  },

  playerReveal: {
    fontFamily: FONT_FAMILIES.DISPLAY,
    fontWeight: 800,
    fontSize: 92, // Scale range 82–100px
    lineHeight: 0.95,
    maxLines: 1,
    textTransform: 'uppercase',
    color: '#FACC15',
    shadow: '0 6px 20px rgba(0,0,0,0.85)',
    description: 'Subject name reveal when focal player appears',
  },

  supportingHeadline: {
    fontFamily: FONT_FAMILIES.READING,
    fontWeight: 600,
    fontSize: 36, // Scale range 34–40px
    lineHeight: 1.12,
    maxLines: 2,
    textTransform: 'none',
    color: '#E2E8F0',
    description: 'Contextual subheadline beneath main headline',
  },

  narrationSubtitle: {
    fontFamily: FONT_FAMILIES.READING,
    fontWeight: 600,
    fontSize: 46, // Scale range 44–48px
    lineHeight: 1.16,
    maxLines: 2,
    maxCharsPerLine: 36,
    textTransform: 'none',
    color: '#FFFFFF',
    shadow: '0 2px 8px rgba(0,0,0,0.9)',
    description: 'Sentence-case narration subtitles aligned to speech',
  },

  statisticHero: {
    fontFamily: FONT_FAMILIES.DISPLAY,
    fontWeight: 800,
    fontSize: 124, // Scale range 112–140px
    lineHeight: 0.92,
    maxLines: 1,
    textTransform: 'uppercase',
    color: '#38BDF8',
    description: 'Large hero statistic or transfer value (e.g. €60M, 155 MINS)',
  },

  statisticLabel: {
    fontFamily: FONT_FAMILIES.MONO,
    fontWeight: 500,
    fontSize: 26, // Scale range 24–28px
    lineHeight: 1.15,
    textTransform: 'uppercase',
    color: '#94A3B8',
    description: 'Technical label accompanying hero statistic (e.g. REPORTED FEE)',
  },

  lowerThird: {
    fontFamily: FONT_FAMILIES.READING,
    fontWeight: 600,
    fontSize: 36,
    lineHeight: 1.15,
    maxLines: 2,
    textTransform: 'none',
    color: '#FFFFFF',
    description: 'Two-tier broadcast lower-third headline',
  },

  tickerText: {
    fontFamily: FONT_FAMILIES.READING,
    fontWeight: 600,
    fontSize: 30,
    lineHeight: 1.1,
    textTransform: 'uppercase',
    color: '#FFFFFF',
    description: 'Continuous rolling news ticker channel',
  },

  sourceMetadata: {
    fontFamily: FONT_FAMILIES.MONO,
    fontWeight: 500,
    fontSize: 20, // Scale range 18–22px
    lineHeight: 1.15,
    textTransform: 'uppercase',
    color: '#64748B',
    description: 'Source attribution, photo wire provenance & timecodes',
  },

  outroHeadline: {
    fontFamily: FONT_FAMILIES.DISPLAY,
    fontWeight: 700,
    fontSize: 64,
    lineHeight: 1.0,
    textTransform: 'uppercase',
    color: '#FFFFFF',
    description: 'Outro closing plate headline',
  },

  outroCTA: {
    fontFamily: FONT_FAMILIES.READING,
    fontWeight: 600,
    fontSize: 26,
    lineHeight: 1.2,
    textTransform: 'none',
    color: '#94A3B8',
    description: 'Outro call to action and social handles',
  },
};

/**
 * Telegram Scene Chart Typography Scale (for 1920-wide canvas)
 */
export const TELEGRAM_CHART_TYPOGRAPHY = {
  chartTitle: { fontFamily: FONT_FAMILIES.DISPLAY, weight: 700, size: 36 },
  storyHeadline: { fontFamily: FONT_FAMILIES.DISPLAY, weight: 700, size: 34 },
  sceneHeading: { fontFamily: FONT_FAMILIES.DISPLAY, weight: 700, size: 26 },
  dialogueText: { fontFamily: FONT_FAMILIES.READING, weight: 600, size: 25 },
  visualDescription: { fontFamily: FONT_FAMILIES.READING, weight: 400, size: 22 },
  metadata: { fontFamily: FONT_FAMILIES.MONO, weight: 500, size: 19 },
  statusLabel: { fontFamily: FONT_FAMILIES.MONO, weight: 600, size: 20 },
};
