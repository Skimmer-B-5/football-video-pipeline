import React from "react";
import { useCurrentFrame } from "remotion";
import { tokens } from "../design/tokens";

export interface RollingTickerProps {
  text: string;
  badgeLabel?: string;
}

export const RollingTicker: React.FC<RollingTickerProps> = ({
  text,
  badgeLabel = "LATEST NEWS",
}) => {
  const frame = useCurrentFrame();

  // Controlled scroll speed from design tokens
  const scrollOffset = (frame * tokens.layout.ticker.scrollSpeedPxPerFrame) % 3000;

  return (
    <div
      style={{
        position: "absolute",
        left: tokens.layout.ticker.left,
        right: tokens.layout.ticker.right,
        bottom: tokens.layout.ticker.bottom, // LOWERED to 90px to restore 90s TV broadcast layout
        height: tokens.layout.ticker.height,
        display: "flex",
        alignItems: "center",
        zIndex: tokens.layout.ticker.zIndex,
        boxShadow: "0 -4px 18px rgba(0, 0, 0, 0.75)",
        fontFamily: tokens.typography.fontPrimary,
      }}
    >
      {/* Red Ticker Lead Badge */}
      <div
        style={{
          background: tokens.colors.redNews,
          color: tokens.colors.textWhite,
          fontWeight: tokens.typography.weights.black,
          fontSize: tokens.typography.sizes.tickerText - 1,
          letterSpacing: tokens.typography.letterSpacing.wide,
          padding: "0 22px",
          height: "100%",
          display: "flex",
          alignItems: "center",
          zIndex: 2,
          whiteSpace: "nowrap",
          boxShadow: "4px 0 12px rgba(0, 0, 0, 0.5)",
          textTransform: "uppercase",
        }}
      >
        {badgeLabel}
      </div>

      {/* Navy Rolling Text Container */}
      <div
        style={{
          flex: 1,
          height: "100%",
          background: tokens.colors.navyCardOpaque,
          borderTop: `1px solid ${tokens.colors.yellowSubtle}`,
          borderBottom: `1px solid ${tokens.colors.yellowSubtle}`,
          overflow: "hidden",
          position: "relative",
          display: "flex",
          alignItems: "center",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: tokens.canvas.width - scrollOffset,
            whiteSpace: "nowrap",
            color: tokens.colors.textWhite,
            fontWeight: tokens.typography.weights.bold,
            fontSize: tokens.typography.sizes.tickerText,
            letterSpacing: tokens.typography.letterSpacing.normal,
            textTransform: "uppercase",
          }}
        >
          {text} &nbsp;&nbsp;✦&nbsp;&nbsp; {text} &nbsp;&nbsp;✦&nbsp;&nbsp; {text}
        </div>
      </div>
    </div>
  );
};
