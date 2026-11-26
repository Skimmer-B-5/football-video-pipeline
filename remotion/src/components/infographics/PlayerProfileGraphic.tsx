import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface PlayerProfileGraphicProps {
  player_name?: string;
  club?: string;
  nationality?: string;
  age?: number | string;
  position?: string;
  market_value?: string;
  contract_until?: string;
  key_traits?: string[];
}

export const PlayerProfileGraphic: React.FC<PlayerProfileGraphicProps> = ({
  player_name = "TARGET PLAYER",
  club = "CURRENT SQUAD",
  nationality = "BRAZIL",
  age = 18,
  position = "CENTRE-FORWARD",
  market_value = "€60,000,000",
  contract_until = "JUNE 2030",
  key_traits = ["BALL STRIKING", "PHYSICAL POWER", "EXPLOSIVE PACE"],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: tokens.animation.springSmooth,
  });

  return (
    <div
      style={{
        position: "absolute",
        top: tokens.layout.stage.top + 10,
        left: tokens.layout.stage.left,
        right: tokens.layout.stage.right,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        zIndex: tokens.layout.stage.zIndex,
      }}
    >
      <div
        style={{
          width: "100%",
          background: tokens.colors.navyCard,
          border: `2px solid ${tokens.colors.yellowSubtle}`,
          borderLeft: `8px solid ${tokens.colors.yellowHighlight}`,
          borderRadius: 12,
          padding: "24px 22px",
          boxShadow: tokens.colors.shadowHeavy,
          transform: `scale(${0.92 + entrance * 0.08})`,
          opacity: Math.min(entrance * 1.5, 1),
          fontFamily: tokens.typography.fontPrimary,
        }}
      >
        {/* Header Ribbon */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            borderBottom: "1px solid rgba(255, 209, 102, 0.25)",
            paddingBottom: 10,
            marginBottom: 16,
          }}
        >
          <div>
            <div style={{ color: tokens.colors.yellowHighlight, fontSize: 16, fontWeight: 800, textTransform: "uppercase" }}>
              {nationality} ✦ {position}
            </div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 34, fontWeight: 900, textTransform: "uppercase" }}>
              {player_name}
            </div>
          </div>
          <div
            style={{
              background: tokens.colors.redNews,
              color: tokens.colors.textWhite,
              fontSize: 18,
              fontWeight: 900,
              padding: "4px 12px",
              borderRadius: 4,
            }}
          >
            {club}
          </div>
        </div>

        {/* 2-Column Info Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 12,
            marginBottom: 16,
          }}
        >
          <div style={{ background: tokens.colors.navyCardLight, borderRadius: 8, padding: "12px 14px" }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: 16, textTransform: "uppercase" }}>AGE / STATUS</div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 26, fontWeight: 900 }}>{age} YEARS OLD</div>
          </div>

          <div style={{ background: tokens.colors.navyCardLight, borderRadius: 8, padding: "12px 14px" }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: 16, textTransform: "uppercase" }}>CONTRACT EXPIRY</div>
            <div style={{ color: tokens.colors.cyanTactical, fontSize: 26, fontWeight: 900 }}>{contract_until}</div>
          </div>
        </div>

        {/* Market Value Card */}
        <div
          style={{
            background: "linear-gradient(90deg, #1C2541 0%, #2A3B66 100%)",
            borderLeft: `6px solid ${tokens.colors.yellowHighlight}`,
            borderRadius: 8,
            padding: "12px 18px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 16,
          }}
        >
          <div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 18, fontWeight: 800, textTransform: "uppercase" }}>
              ESTIMATED MARKET VALUATION
            </div>
            <div style={{ color: tokens.colors.textMuted, fontSize: 15 }}>Transfermarkt Benchmark</div>
          </div>
          <div style={{ color: tokens.colors.yellowHighlight, fontSize: 36, fontWeight: 900 }}>
            {market_value}
          </div>
        </div>

        {/* Key Strengths Badges */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {key_traits.map((trait, idx) => (
            <span
              key={idx}
              style={{
                background: "rgba(255, 209, 102, 0.15)",
                color: tokens.colors.yellowHighlight,
                border: "1px solid rgba(255, 209, 102, 0.4)",
                padding: "4px 12px",
                borderRadius: 4,
                fontSize: 16,
                fontWeight: 800,
                letterSpacing: "0.5px",
                textTransform: "uppercase",
              }}
            >
              ✦ {trait}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
