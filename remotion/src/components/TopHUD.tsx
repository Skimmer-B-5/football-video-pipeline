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

  // Subtle spring entry for HUD
  const hudProgress = spring({
    frame,
    fps,
    config: tokens.animation.springBrisk,
  });

  const translateY = (1 - hudProgress) * -20;
  const opacity = Math.min(hudProgress, 1);

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
        transform: `translateY(${translateY}px)`,
        opacity,
        fontFamily: tokens.typography.fontPrimary,
      }}
    >
      {/* Top-Left: Channel Bezel Logo Bug */}
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
              color: tokens.colors.textWhite,
              fontWeight: tokens.typography.weights.extraBold,
              fontSize: tokens.typography.sizes.hudBadge + 2,
              letterSpacing: tokens.typography.letterSpacing.wide,
              textTransform: "uppercase",
            }}
          >
            30 FOOTBALL PLUS
          </span>
        </div>
      )}

      {/* Top-Right: Truthful Category Kicker / Status Indicator */}
      <div
        style={{
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
            color: tokens.colors.yellowHighlight,
            fontWeight: tokens.typography.weights.extraBold,
            fontSize: tokens.typography.sizes.hudBadge,
            letterSpacing: tokens.typography.letterSpacing.wide,
            textTransform: "uppercase",
          }}
        >
          {kicker || "TRANSFER WATCH"}
        </span>
      </div>
    </div>
  );
};
