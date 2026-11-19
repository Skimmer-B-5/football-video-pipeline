import React from "react";
import { useCurrentFrame } from "remotion";
import { tokens } from "../design/tokens";

export interface RollingTickerProps {
  text: string;
  badgeLabel?: string;
  tickerBaseSrc?: string;
  headlinesTabSrc?: string;
}

export const RollingTicker: React.FC<RollingTickerProps> = ({
  text,
  badgeLabel = "HEADLINES",
  tickerBaseSrc,
  headlinesTabSrc,
}) => {
  const frame = useCurrentFrame();

  // Controlled scroll speed from design tokens
  const scrollOffset = (frame * tokens.layout.ticker.scrollSpeedPxPerFrame) % 3000;

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: tokens.layout.ticker.bottom, // LOWERED to 90px to restore 90s TV broadcast layout
        height: 110,
        zIndex: tokens.layout.ticker.zIndex,
        overflow: "hidden",
        borderTop: "2px solid rgba(255, 209, 102, 0.45)",
        boxShadow: "0 -4px 18px rgba(0, 0, 0, 0.75)",
        fontFamily: tokens.typography.fontPrimary,
      }}
    >
      {/* 1. 3D Ticker Base Plate */}
      {tickerBaseSrc ? (
        <img
          src={tickerBaseSrc}
          alt="Ticker Base"
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: 1080,
            height: 110,
            objectFit: "cover",
          }}
        />
      ) : (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: 110,
            background: "linear-gradient(180deg, #09122C 0%, #050B1B 60%, #000000 100%)",
            borderTop: "3px solid #D90429",
          }}
        />
      )}

      {/* 2. 3D Red Headlines Tab on Left */}
      {headlinesTabSrc ? (
        <img
          src={headlinesTabSrc}
          alt="Headlines"
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: 280,
            height: 110,
            zIndex: 5,
          }}
        />
      ) : (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: 260,
            height: 110,
            background: "#D90429",
            color: "#FFFFFF",
            fontWeight: 900,
            fontSize: 26,
            letterSpacing: "2px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 5,
            boxShadow: "4px 0 14px rgba(0, 0, 0, 0.6)",
          }}
        >
          {badgeLabel}
        </div>
      )}

      {/* 3. Rolling Ticker Text Strictly Bounded (Starts at right edge of Headlines tab at x: 280) */}
      <div
        style={{
          position: "absolute",
          left: 280,
          right: 0,
          bottom: 0,
          height: 110,
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          zIndex: 3,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 800 - scrollOffset,
            whiteSpace: "nowrap",
            color: "#FFFFFF",
            fontWeight: 800,
            fontSize: 26,
            letterSpacing: "1.5px",
            textTransform: "uppercase",
          }}
        >
          {text} &nbsp;&nbsp;✦&nbsp;&nbsp; {text} &nbsp;&nbsp;✦&nbsp;&nbsp; {text}
        </div>
      </div>
    </div>
  );
};
