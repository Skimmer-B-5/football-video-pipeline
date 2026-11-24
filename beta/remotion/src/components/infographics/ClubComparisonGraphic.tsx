import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface ComparisonMetric {
  label: string;
  val_a: string | number;
  val_b: string | number;
}

export interface ClubComparisonGraphicProps {
  club_a?: { name: string; badge_color?: string };
  club_b?: { name: string; badge_color?: string };
  metrics?: ComparisonMetric[];
}

export const ClubComparisonGraphic: React.FC<ClubComparisonGraphicProps> = ({
  club_a = { name: "CLUB A", badge_color: "#D90429" },
  club_b = { name: "CLUB B", badge_color: "#48CAE4" },
  metrics = [
    { label: "LEAGUE POSITION", val_a: "2ND", val_b: "1ST" },
    { label: "GOALS SCORED", val_a: "48", val_b: "54" },
    { label: "EXPECTED GOALS (xG)", val_a: "44.2", val_b: "49.8" },
    { label: "CLEAN SHEETS", val_a: "11", val_b: "9" },
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
        {/* Title */}
        <div
          style={{
            textAlign: "center",
            color: tokens.colors.yellowHighlight,
            fontSize: 22,
            fontWeight: 900,
            letterSpacing: "2px",
            textTransform: "uppercase",
            marginBottom: 14,
          }}
        >
          HEAD-TO-HEAD COMPARATIVE DATA
        </div>

        {/* Club Comparison Header */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr auto 1fr",
            alignItems: "center",
            background: tokens.colors.navyCardLight,
            borderRadius: 8,
            padding: "12px 16px",
            marginBottom: 18,
          }}
        >
          <div style={{ textAlign: "center" }}>
            <div style={{ color: tokens.colors.textWhite, fontSize: 26, fontWeight: 900, textTransform: "uppercase" }}>
              {club_a.name}
            </div>
          </div>
          <div style={{ color: tokens.colors.yellowHighlight, fontSize: 24, fontWeight: 900, padding: "0 14px" }}>
            VS
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: tokens.colors.cyanTactical, fontSize: 26, fontWeight: 900, textTransform: "uppercase" }}>
              {club_b.name}
            </div>
          </div>
        </div>

        {/* Metrics List */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {metrics.map((m, idx) => {
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
                  gridTemplateColumns: "80px 1fr 80px",
                  alignItems: "center",
                  transform: `translateY(${(1 - Math.min(rowEntrance, 1)) * 10}px)`,
                  opacity: Math.min(rowEntrance, 1),
                }}
              >
                <div style={{ color: tokens.colors.textWhite, fontSize: 28, fontWeight: 900, textAlign: "center" }}>
                  {m.val_a}
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
                  {m.label}
                </div>
                <div style={{ color: tokens.colors.cyanTactical, fontSize: 28, fontWeight: 900, textAlign: "center" }}>
                  {m.val_b}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
