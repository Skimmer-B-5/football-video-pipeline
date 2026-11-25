import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../design/tokens";

export interface TopHUDProps {
  kicker: string;
  logoSrc?: string;
}

export const TopHUD: React.FC<TopHUDProps> = ({ kicker, logoSrc }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Coordinated Opening Entrance (Section 3)
  // 1. Logo entrance: slides in horizontally from the left (frames 0 to 12, ~400ms ease-out)
  const logoProgress = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 120 },
  });
  const logoTranslateX = (1 - logoProgress) * -320;
  const logoOpacity = Math.min(logoProgress * 1.6, 1);

  // 2. Kicker entrance: slides in horizontally from the right with stagger (frames 4 to 16, ~400ms ease-out)
  const kickerProgress = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 120 },
  });
  const kickerTranslateX = (1 - kickerProgress) * 320;
  const kickerOpacity = Math.min(kickerProgress * 1.6, 1);

  // Display wording: TRANSFER WATCH (not TRANSFER REPORT), strip any leading bullet to avoid double dot with HUD indicator
  const rawKicker = (kicker || "TRANSFER WATCH").replace(/^[●•○\s]+/, "").trim();
  const displayKicker = rawKicker && !rawKicker.includes("REPORT") ? rawKicker : "TRANSFER WATCH";

  return (
    <div
      style={{
        position: "absolute",
        top: tokens.layout.topHud.top,
        left: tokens.layout.topHud.left,
        right: tokens.layout.topHud.right,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        zIndex: tokens.layout.topHud.zIndex,
        fontFamily: tokens.typography.fontPrimary,
      }}
    >
      {/* Top-Left: Channel Bezel Logo Bug (Slides from Left) */}
      <div
        style={{
          transform: `translateX(${logoTranslateX}px)`,
          opacity: logoOpacity,
        }}
      >
        {logoSrc ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              filter: "drop-shadow(0 6px 18px rgba(0, 0, 0, 0.85))",
            }}
          >
            <img
              src={logoSrc}
              alt="30 Football Plus"
              style={{
                height: tokens.layout.topHud.height,
                width: "auto",
                objectFit: "contain",
              }}
            />
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              background: tokens.colors.navyCard,
              padding: "8px 16px",
              borderLeft: `4px solid ${tokens.colors.redNews}`,
              borderRadius: 4,
              boxShadow: tokens.colors.shadowCard,
            }}
          >
            <span
              style={{
                background: tokens.colors.redNews,
                color: tokens.colors.textWhite,
                fontWeight: tokens.typography.weights.black,
                fontSize: tokens.typography.sizes.hudBadge,
                padding: "2px 8px",
                borderRadius: 2,
                letterSpacing: tokens.typography.letterSpacing.normal,
              }}
            >
              30+
            </span>
            <span
              style={{
                fontFamily: tokens.typography.fontDisplay,
                color: tokens.colors.textWhite,
                fontWeight: tokens.typography.weights.bold,
                fontSize: tokens.typography.sizes.hudBadge + 4,
                letterSpacing: tokens.typography.letterSpacing.normal,
                textTransform: "uppercase",
              }}
            >
              30 FOOTBALL PLUS
            </span>
          </div>
        )}
      </div>

      {/* Top-Right: Truthful Category Kicker / Status Indicator (Slides from Right) */}
      <div
        style={{
          transform: `translateX(${kickerTranslateX}px)`,
          opacity: kickerOpacity,
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: tokens.colors.navyCard,
          padding: "8px 18px",
          borderRight: `4px solid ${tokens.colors.yellowHighlight}`,
          borderRadius: 4,
          boxShadow: tokens.colors.shadowCard,
        }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: tokens.colors.yellowHighlight,
            boxShadow: tokens.colors.shadowGlowYellow,
          }}
        />
        <span
          style={{
            fontFamily: tokens.typography.fontMono,
            color: tokens.colors.yellowHighlight,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.hudBadge,
            letterSpacing: "1.2px",
            textTransform: "uppercase",
          }}
        >
          {displayKicker}
        </span>
      </div>
    </div>
  );
};
