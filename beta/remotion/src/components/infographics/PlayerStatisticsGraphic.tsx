import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface StatItem {
  label: string;
  value: string | number;
  highlight?: boolean;
  subtext?: string;
}

export interface PlayerStatisticsGraphicProps {
  player_name?: string;
  club?: string;
  season?: string;
  stats?: StatItem[];
}

export const PlayerStatisticsGraphic: React.FC<PlayerStatisticsGraphicProps> = ({
  player_name = "PLAYER NAME",
  club = "CLUB",
  season = "2024/25 CAMPAIGN",
  stats = [
    { label: "GOALS", value: "24", highlight: true, subtext: "Top Scorer" },
    { label: "ASSISTS", value: "11", highlight: false, subtext: "All Comps" },
    { label: "MINS PER GOAL", value: "88'", highlight: true, subtext: "Elite Rate" },
    { label: "EXPECTED GOALS (xG)", value: "19.4", highlight: false, subtext: "+4.6 Overperf." },
  ],
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
          borderLeft: `8px solid ${tokens.colors.redNews}`,
          borderRadius: 12,
          padding: "24px 22px",
          boxShadow: tokens.colors.shadowHeavy,
          transform: `scale(${0.92 + entrance * 0.08})`,
          opacity: Math.min(entrance * 1.5, 1),
          fontFamily: tokens.typography.fontPrimary,
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            borderBottom: "1px solid rgba(255, 209, 102, 0.25)",
            paddingBottom: 10,
            marginBottom: 18,
          }}
        >
          <div>
            <div style={{ color: tokens.colors.yellowHighlight, fontSize: 16, fontWeight: 800, textTransform: "uppercase" }}>
              {season} ✦ {club}
            </div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 34, fontWeight: 900, textTransform: "uppercase" }}>
              {player_name}
            </div>
          </div>
          <div
            style={{
              background: tokens.colors.redNews,
              color: tokens.colors.textWhite,
              fontSize: 16,
              fontWeight: 900,
              padding: "4px 10px",
              borderRadius: 4,
              letterSpacing: "1px",
            }}
          >
            PERFORMANCE METRICS
          </div>
        </div>

        {/* 2x2 Stats Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 14,
          }}
        >
          {stats.slice(0, 4).map((item, idx) => {
            const itemDelay = frame - (idx + 1) * 3;
            const itemEntrance = spring({
              frame: Math.max(0, itemDelay),
              fps,
              config: tokens.animation.springBrisk,
            });

            return (
              <div
                key={idx}
                style={{
                  background: item.highlight
                    ? "linear-gradient(180deg, #1C2541 0%, #251B38 100%)"
                    : tokens.colors.navyCardLight,
                  border: item.highlight
                    ? `1px solid ${tokens.colors.yellowHighlight}`
                    : "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: 8,
                  padding: "16px 14px",
                  textAlign: "center",
                  transform: `translateY(${(1 - Math.min(itemEntrance, 1)) * 12}px)`,
                  opacity: Math.min(itemEntrance, 1),
                }}
              >
                <div
                  style={{
                    color: item.highlight ? tokens.colors.yellowHighlight : tokens.colors.textMuted,
                    fontSize: 18,
                    fontWeight: 800,
                    textTransform: "uppercase",
                  }}
                >
                  {item.label}
                </div>
                <div
                  style={{
                    color: item.highlight ? tokens.colors.yellowHighlight : tokens.colors.textWhite,
                    fontSize: 44,
                    fontWeight: 900,
                    marginTop: 2,
                    letterSpacing: "0.5px",
                  }}
                >
                  {item.value}
                </div>
                {item.subtext && (
                  <div style={{ color: tokens.colors.cyanTactical, fontSize: 14, fontWeight: 700, marginTop: 2 }}>
                    {item.subtext}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
