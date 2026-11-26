import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface MatchStatRow {
  label: string;
  home_val: string | number;
  away_val: string | number;
}

export interface MatchStatisticsGraphicProps {
  home_team?: string;
  away_team?: string;
  home_score?: number;
  away_score?: number;
  competition?: string;
  stats?: MatchStatRow[];
}

export const MatchStatisticsGraphic: React.FC<MatchStatisticsGraphicProps> = ({
  home_team = "ARSENAL",
  away_team = "PARIS SG",
  home_score = 2,
  away_score = 0,
  competition = "UEFA CHAMPIONS LEAGUE",
  stats = [
    { label: "POSSESSION", home_val: "47%", away_val: "53%" },
    { label: "SHOTS (ON TARGET)", home_val: "6 (5)", away_val: "10 (2)" },
    { label: "EXPECTED GOALS (xG)", home_val: "1.82", away_val: "0.64" },
    { label: "BIG CHANCES", home_val: "3", away_val: "1" },
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
        {/* Competition Banner */}
        <div
          style={{
            textAlign: "center",
            color: tokens.colors.yellowHighlight,
            fontSize: 20,
            fontWeight: 900,
            letterSpacing: "2px",
            textTransform: "uppercase",
            borderBottom: "1px solid rgba(255, 209, 102, 0.25)",
            paddingBottom: 8,
            marginBottom: 14,
          }}
        >
          {competition} ✦ FULL-TIME RESULT
        </div>

        {/* Scoreline Banner */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr auto 1fr",
            alignItems: "center",
            background: tokens.colors.navyCardLight,
            borderRadius: 8,
            padding: "16px 14px",
            marginBottom: 16,
          }}
        >
          <div style={{ textAlign: "center" }}>
            <div style={{ color: tokens.colors.textWhite, fontSize: 30, fontWeight: 900, textTransform: "uppercase" }}>
              {home_team}
            </div>
          </div>
          <div
            style={{
              background: tokens.colors.redNews,
              color: tokens.colors.textWhite,
              fontSize: 44,
              fontWeight: 900,
              padding: "4px 22px",
              borderRadius: 6,
              letterSpacing: "3px",
              boxShadow: tokens.colors.shadowGlowRed,
            }}
          >
            {home_score} - {away_score}
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: tokens.colors.cyanTactical, fontSize: 30, fontWeight: 900, textTransform: "uppercase" }}>
              {away_team}
            </div>
          </div>
        </div>

        {/* Match Metrics Table */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {stats.map((row, idx) => {
            const delay = frame - idx * 4;
            const rowEntrance = spring({
              frame: Math.max(0, delay),
              fps,
              config: tokens.animation.springBrisk,
            });

            return (
              <div
                key={idx}
                style={{
                  background: "rgba(28, 37, 65, 0.7)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: 6,
                  padding: "10px 14px",
                  display: "grid",
                  gridTemplateColumns: "90px 1fr 90px",
                  alignItems: "center",
                  transform: `translateY(${(1 - Math.min(rowEntrance, 1)) * 10}px)`,
                  opacity: Math.min(rowEntrance, 1),
                }}
              >
                <div style={{ color: tokens.colors.textWhite, fontSize: 26, fontWeight: 900, textAlign: "center" }}>
                  {row.home_val}
                </div>
                <div
                  style={{
                    color: tokens.colors.yellowHighlight,
                    fontSize: 18,
                    fontWeight: 800,
                    textAlign: "center",
                    textTransform: "uppercase",
                  }}
                >
                  {row.label}
                </div>
                <div style={{ color: tokens.colors.cyanTactical, fontSize: 26, fontWeight: 900, textAlign: "center" }}>
                  {row.away_val}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
