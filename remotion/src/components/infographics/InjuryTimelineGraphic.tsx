import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface InjuryTimelineGraphicProps {
  player_name?: string;
  club?: string;
  diagnosis?: string;
  matches_missed?: string | number;
  expected_return?: string;
  status?: string;
  progress_percentage?: number;
}

export const InjuryTimelineGraphic: React.FC<InjuryTimelineGraphicProps> = ({
  player_name = "PLAYER NAME",
  club = "CLUB",
  diagnosis = "HAMSTRING TEAR (GRADE 2)",
  matches_missed = 6,
  expected_return = "EARLY FEBRUARY 2025",
  status = "LIGHT PITCH WORK",
  progress_percentage = 65,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: tokens.animation.springSmooth,
  });

  const barWidth = spring({
    frame: frame - 6,
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
          borderLeft: `8px solid ${tokens.colors.amberRumour}`,
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
            marginBottom: 16,
          }}
        >
          <div>
            <div style={{ color: tokens.colors.amberRumour, fontSize: 16, fontWeight: 800, textTransform: "uppercase" }}>
              MEDICAL & RECOVERY BULLETIN
            </div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 32, fontWeight: 900, textTransform: "uppercase" }}>
              {player_name}
            </div>
          </div>
          <div
            style={{
              background: tokens.colors.amberRumour,
              color: tokens.colors.navyPrimary,
              fontSize: 16,
              fontWeight: 900,
              padding: "4px 12px",
              borderRadius: 4,
            }}
          >
            {club}
          </div>
        </div>

        {/* Diagnosis Card */}
        <div
          style={{
            background: tokens.colors.navyCardLight,
            border: "1px solid rgba(255, 255, 255, 0.12)",
            borderRadius: 8,
            padding: "12px 16px",
            marginBottom: 16,
          }}
        >
          <div style={{ color: tokens.colors.textMuted, fontSize: 16, textTransform: "uppercase" }}>DIAGNOSED INJURY</div>
          <div style={{ color: tokens.colors.yellowHighlight, fontSize: 24, fontWeight: 900, textTransform: "uppercase" }}>
            {diagnosis}
          </div>
        </div>

        {/* 2-Column Stats (Matches Missed vs Expected Return) */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 12,
            marginBottom: 16,
          }}
        >
          <div
            style={{
              background: tokens.colors.navyCardLight,
              borderRadius: 8,
              padding: "12px",
              textAlign: "center",
            }}
          >
            <div style={{ color: tokens.colors.textMuted, fontSize: 16, fontWeight: 700 }}>MATCHES MISSED</div>
            <div style={{ color: tokens.colors.redNews, fontSize: 36, fontWeight: 900 }}>{matches_missed} FIXTURES</div>
          </div>
          <div
            style={{
              background: tokens.colors.navyCardLight,
              borderRadius: 8,
              padding: "12px",
              textAlign: "center",
            }}
          >
            <div style={{ color: tokens.colors.textMuted, fontSize: 16, fontWeight: 700 }}>PROJECTED RETURN</div>
            <div style={{ color: tokens.colors.greenOfficial, fontSize: 28, fontWeight: 900, marginTop: 4 }}>
              {expected_return}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ color: tokens.colors.textWhite, fontSize: 18, fontWeight: 800 }}>STAGE: {status}</span>
            <span style={{ color: tokens.colors.yellowHighlight, fontSize: 18, fontWeight: 900 }}>
              {progress_percentage}% RECOVERED
            </span>
          </div>
          <div
            style={{
              height: 14,
              background: "rgba(255, 255, 255, 0.15)",
              borderRadius: 7,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${Math.min(100, Math.max(0, progress_percentage)) * Math.min(barWidth, 1)}%`,
                background: "linear-gradient(90deg, #F77F00 0%, #06D6A0 100%)",
                borderRadius: 7,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
