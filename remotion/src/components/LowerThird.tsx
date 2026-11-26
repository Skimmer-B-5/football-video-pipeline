import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneOnScreen } from "../types";
import { tokens } from "../design/tokens";

export interface LowerThirdProps {
  onScreen: SceneOnScreen;
}

export const LowerThird: React.FC<LowerThirdProps> = ({ onScreen }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Snappy spring entrance for lower third
  const entrance = spring({
    frame,
    fps,
    config: tokens.animation.springSmooth,
  });

  const translateX = (1 - entrance) * -70;
  const opacity = Math.min(entrance * 1.5, 1);

  const { headline, subheadline, data_callout, status_badge, source_credit } = onScreen;

  // Determine badge color theme
  const getBadgeBg = (badge?: string) => {
    switch (badge?.toUpperCase()) {
      case "OFFICIAL":
      case "CONFIRMED":
        return tokens.colors.greenOfficial;
      case "RUMOUR":
      case "REPORT":
        return tokens.colors.amberRumour;
      case "TACTICAL":
        return tokens.colors.cyanTactical;
      case "BREAKING":
      case "EXCLUSIVE":
      default:
        return tokens.colors.redNews;
    }
  };

  return (
    <div
      style={{
        position: "absolute",
        left: tokens.layout.lowerThird.left,
        right: tokens.layout.lowerThird.right,
        bottom: tokens.layout.lowerThird.bottom, // Resting cleanly above the ticker
        maxHeight: tokens.layout.lowerThird.maxHeight,
        transform: `translateX(${translateX}px)`,
        opacity,
        zIndex: tokens.layout.lowerThird.zIndex,
        fontFamily: tokens.typography.fontPrimary,
      }}
    >
      <div
        style={{
          background: tokens.colors.navyCard,
          borderLeft: `8px solid ${tokens.colors.redNews}`,
          borderRadius: "0 8px 8px 0",
          padding: "18px 24px",
          boxShadow: tokens.colors.shadowHeavy,
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        {/* Top Badges Row */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", fontFamily: tokens.typography.fontMono }}>
          {status_badge && (
            <span
              style={{
                background: getBadgeBg(status_badge),
                color: status_badge.toUpperCase() === "OFFICIAL" || status_badge.toUpperCase() === "TACTICAL"
                  ? tokens.colors.navyPrimary
                  : tokens.colors.textWhite,
                fontSize: tokens.typography.sizes.hudBadge,
                fontWeight: tokens.typography.weights.semiBold,
                letterSpacing: tokens.typography.letterSpacing.wide,
                padding: "3px 10px",
                borderRadius: 4,
                textTransform: "uppercase",
              }}
            >
              {status_badge}
            </span>
          )}

          {data_callout && (
            <span
              style={{
                background: tokens.colors.yellowHighlight,
                color: tokens.colors.navyPrimary,
                fontSize: tokens.typography.sizes.statisticLabel,
                fontWeight: tokens.typography.weights.semiBold,
                letterSpacing: tokens.typography.letterSpacing.normal,
                padding: "3px 10px",
                borderRadius: 4,
                textTransform: "uppercase",
              }}
            >
              {data_callout}
            </span>
          )}

          {source_credit && (
            <span
              style={{
                color: tokens.colors.textMuted,
                fontSize: tokens.typography.sizes.sourceMetadata,
                fontWeight: tokens.typography.weights.medium,
                letterSpacing: "0.5px",
                textTransform: "uppercase",
                marginLeft: "auto",
              }}
            >
              SRC: {source_credit}
            </span>
          )}
        </div>

        {/* Primary Broadcast Headline (Barlow Condensed ExtraBold) */}
        <div
          style={{
            fontFamily: tokens.typography.fontDisplay,
            color: tokens.colors.textWhite,
            fontWeight: tokens.typography.weights.extraBold,
            fontSize: headline.length > 36 ? tokens.typography.sizes.headlineMedium : tokens.typography.sizes.headlineLarge,
            lineHeight: tokens.typography.lineHeights.headline,
            letterSpacing: tokens.typography.letterSpacing.tight,
            textTransform: "uppercase",
            textShadow: "0 2px 10px rgba(0, 0, 0, 0.9)",
            overflow: "hidden",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
          }}
        >
          {headline}
        </div>

        {/* Supporting Secondary Headline (Inter SemiBold) */}
        {subheadline && (
          <div
            style={{
              fontFamily: tokens.typography.fontReading,
              color: tokens.colors.yellowHighlight,
              fontWeight: tokens.typography.weights.semiBold,
              fontSize: tokens.typography.sizes.subheadline,
              lineHeight: tokens.typography.lineHeights.subheadline,
              letterSpacing: tokens.typography.letterSpacing.normal,
              textTransform: "none",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {subheadline}
          </div>
        )}
      </div>
    </div>
  );
};
