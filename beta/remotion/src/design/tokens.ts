/**
 * tokens.ts - Central Design Tokens for 30 Football Plus Engine
 * 
 * Reusable visual, layout, typography, animation, and CRT broadcast tokens.
 * All Remotion components must consume these tokens to ensure visual consistency
 * across every football story format.
 */

export const tokens = {
  // 1. Canvas Dimensions (9:16 Vertical Broadcast)
  canvas: {
    width: 1080,
    height: 1920,
    fps: 30,
    aspectRatio: "9:16",
  },

  // 2. Safe Areas (Strict platform margins for YouTube Shorts / TikTok / Reels)
  safeArea: {
    top: 80,
    bottom: 90,
    left: 55,
    right: 55,
  },

  // 3. Layout Anchors & Positions (Coordinates in 1080x1920 space)
  layout: {
    // Channel Bug / Top HUD
    topHud: {
      top: 80,
      left: 55,
      right: 55,
      height: 105,
      zIndex: 60,
    },

    // Central Stage (Reserved for 9:16 Photography & Vertical Infographics)
    stage: {
      top: 210,
      bottom: 580, // Leaves 1130px height of unobstructed view
      left: 55,
      right: 55,
      zIndex: 20,
    },

    // Subtitle Cards (Floating cleanly above lower third)
    subtitles: {
      bottom: 540,
      left: 70,
      right: 70,
      maxHeight: 120,
      zIndex: 45,
    },

    // Reusable Two-Tier Broadcast Lower-Third
    lowerThird: {
      bottom: 210, // Anchored directly above ticker band
      left: 70,
      right: 70,
      maxHeight: 310,
      zIndex: 40,
    },

    // Rolling Factual News Ticker (LOWERED to restore 90s TV broadcast proportions)
    ticker: {
      bottom: 90, // Resting cleanly above 80px platform safe margin
      height: 110,
      left: 0,
      right: 0,
      zIndex: 50,
      badgeWidth: 280,
      scrollSpeedPxPerFrame: 4.5,
    },

    // Retro CRT & Tube Overlay (Top-most visual post-processing layer)
    crtOverlay: {
      zIndex: 75,
    },
  },

  // 4. Color Palette (Late-90s / Early-2000s TV Football News Identity)
  colors: {
    // Primary Broadcast Navies
    navyPrimary: "#0B132B",
    navyCard: "rgba(11, 19, 43, 0.94)",
    navyCardOpaque: "#0B132B",
    navyCardLight: "#1C2541",
    navyAccent: "#2A3B66",
    navyGlass: "rgba(11, 19, 43, 0.88)",

    // Signature News Accents
    redNews: "#D90429",
    redDark: "#9B0014",
    redGlow: "rgba(217, 4, 41, 0.5)",

    // High-Contrast Highlights
    yellowHighlight: "#FFD166",
    yellowSubtle: "rgba(255, 209, 102, 0.35)",

    // Category / State Badges
    amberRumour: "#F77F00",
    greenOfficial: "#06D6A0",
    cyanTactical: "#48CAE4",
    purpleAnalysis: "#7209B7",

    // Monochromes & Text
    textWhite: "#FFFFFF",
    textOffWhite: "#E0E6ED",
    textMuted: "#A0AAB2",
    textDark: "#0B132B",

    // Borders & Glassmorphism
    borderSubtle: "rgba(255, 209, 102, 0.25)",
    borderSolid: "rgba(255, 255, 255, 0.15)",
    shadowHeavy: "0 14px 40px rgba(0, 0, 0, 0.85)",
    shadowCard: "0 8px 24px rgba(0, 0, 0, 0.65)",
    shadowGlowYellow: "0 0 16px rgba(255, 209, 102, 0.4)",
    shadowGlowRed: "0 0 16px rgba(217, 4, 41, 0.5)",
  },

  // 5. Permanent Typography System (V7.1.3 Single Source of Truth)
  typography: {
    fontDisplay: "'Barlow Condensed', sans-serif",
    fontReading: "'Inter', sans-serif",
    fontMono: "'IBM Plex Mono', monospace",
    // Legacy aliases for backward compatibility
    fontPrimary: "'Barlow Condensed', sans-serif",
    fontData: "'IBM Plex Mono', monospace",
    weights: {
      regular: 400,
      medium: 500,
      semiBold: 600,
      bold: 700,
      extraBold: 800,
      black: 900,
    },
    sizes: {
      headlineLarge: 78,      // Primary headline scale: 72–84px
      headlineMedium: 66,     // Compact headline for long copy
      playerReveal: 92,       // Subject name reveal: 82–100px
      subheadline: 36,        // Contextual subheadline: 34–40px
      subtitleCard: 46,       // Narration subtitles: 44–48px
      statisticHero: 124,     // Large transfer value: 112–140px
      statisticLabel: 26,     // Technical data label: 24–28px
      hudBadge: 24,           // Status kicker capsule: 22–26px
      lowerThird: 36,         // Lower-third headline: 34–40px
      tickerText: 30,         // News ticker channel: 28–32px
      sourceMetadata: 20,     // Photo / wire attribution: 18–22px
      outroHeadline: 64,      // Outro headline: 56–68px
      outroCTA: 26,           // Outro CTA: 24–28px
      dataCallout: 22,
    },
    letterSpacing: {
      tight: "0px",
      normal: "0.5px",
      wide: "1.2px",
      widest: "1.5px",
    },
    lineHeights: {
      headline: 0.98,
      compact: 1.05,
      subheadline: 1.12,
      subtitle: 1.16,
      mono: 1.15,
      normal: 1.25,
    },
  },

  // 6. Animation Physics (Spring tokens for Remotion)
  animation: {
    springBrisk: {
      damping: 14,
      mass: 0.5,
      stiffness: 130,
    },
    springSmooth: {
      damping: 15,
      mass: 0.7,
      stiffness: 110,
    },
    springStaggerDelayFrames: 6,
    wipeDurationFrames: 12,
    outroDurationFrames: 60,
  },

  // 7. Configurable Retro CRT Visual Layer Settings
  crt: {
    scanlineOpacity: 0.42,
    vignetteIntensity: 0.48,
    flickerDepth: 0.015, // Restrained 1.5% phosphor shimmer
    tubeEdgeReflection: true,
    broadcastSoftness: "contrast(1.04) brightness(0.98) saturate(1.06)",
  },
} as const;

export type DesignTokens = typeof tokens;
