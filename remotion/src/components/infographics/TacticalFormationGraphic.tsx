import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface TacticalFormationGraphicProps {
  formation?: string;
  team_name?: string;
  manager?: string;
  highlight_position?: string;
  role_title?: string;
  role_description?: string;
}

export const TacticalFormationGraphic: React.FC<TacticalFormationGraphicProps> = ({
  formation = "4-3-3",
  team_name = "TEAM TACTICAL SYSTEM",
  manager = "HEAD COACH",
  highlight_position = "CF",
  role_title = "FALSE NINE / DEEP FORWARD",
  role_description = "Drops between lines to create half-space overloads",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: tokens.animation.springSmooth,
  });

  const pulse = Math.sin(frame * 0.25) * 4;

  return (
    <div
      style={{
        position: "absolute",
        top: tokens.layout.stage.top,
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
          borderLeft: `8px solid ${tokens.colors.cyanTactical}`,
          borderRadius: 12,
          padding: "22px 20px",
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
            alignItems: "center",
            borderBottom: "1px solid rgba(255, 209, 102, 0.25)",
            paddingBottom: 8,
            marginBottom: 14,
          }}
        >
          <div>
            <div style={{ color: tokens.colors.cyanTactical, fontSize: 16, fontWeight: 800, textTransform: "uppercase" }}>
              {manager} ✦ TACTICAL BLUEPRINT
            </div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 30, fontWeight: 900, textTransform: "uppercase" }}>
              {team_name}
            </div>
          </div>
          <div
            style={{
              background: tokens.colors.cyanTactical,
              color: tokens.colors.navyPrimary,
              fontSize: 22,
              fontWeight: 900,
              padding: "4px 14px",
              borderRadius: 6,
              letterSpacing: "1px",
            }}
          >
            {formation}
          </div>
        </div>

        {/* Vertical Pitch Canvas Mockup */}
        <div
          style={{
            height: 240,
            background: "linear-gradient(180deg, #16382B 0%, #102B20 100%)",
            border: "2px solid rgba(255, 255, 255, 0.25)",
            borderRadius: 8,
            position: "relative",
            overflow: "hidden",
            marginBottom: 14,
          }}
        >
          {/* Pitch Markings */}
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: 0,
              right: 0,
              height: 2,
              background: "rgba(255, 255, 255, 0.2)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              width: 70,
              height: 70,
              borderRadius: "50%",
              border: "2px solid rgba(255, 255, 255, 0.2)",
              transform: "translate(-50%, -50%)",
            }}
          />
          {/* Penalty Boxes */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: "25%",
              right: "25%",
              height: 40,
              border: "2px solid rgba(255, 255, 255, 0.2)",
              borderTop: "none",
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: "25%",
              right: "25%",
              height: 40,
              border: "2px solid rgba(255, 255, 255, 0.2)",
              borderBottom: "none",
            }}
          />

          {/* Forward Attack Node (Highlighted with pulse) */}
          <div
            style={{
              position: "absolute",
              top: "28%",
              left: "50%",
              transform: `translate(-50%, -50%) scale(${1 + pulse * 0.02})`,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: "50%",
                background: tokens.colors.yellowHighlight,
                color: tokens.colors.navyPrimary,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 20,
                fontWeight: 900,
                boxShadow: "0 0 16px #FFD166",
                border: "2px solid #FFFFFF",
              }}
            >
              {highlight_position}
            </div>
            <div
              style={{
                background: "rgba(11, 19, 43, 0.9)",
                color: tokens.colors.yellowHighlight,
                fontSize: 14,
                fontWeight: 800,
                padding: "2px 8px",
                borderRadius: 4,
                marginTop: 4,
                whiteSpace: "nowrap",
              }}
            >
              KEY ROLE
            </div>
          </div>

          {/* Supporting Formation Nodes */}
          {/* Wingers */}
          <div style={{ position: "absolute", top: "32%", left: "18%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          <div style={{ position: "absolute", top: "32%", right: "18%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          {/* Midfielders */}
          <div style={{ position: "absolute", top: "54%", left: "30%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          <div style={{ position: "absolute", top: "54%", right: "30%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          <div style={{ position: "absolute", top: "62%", left: "50%", transform: "translateX(-50%)", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          {/* Defenders */}
          <div style={{ position: "absolute", bottom: "16%", left: "15%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          <div style={{ position: "absolute", bottom: "16%", left: "38%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          <div style={{ position: "absolute", bottom: "16%", right: "38%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
          <div style={{ position: "absolute", bottom: "16%", right: "15%", width: 28, height: 28, borderRadius: "50%", background: "#FFFFFF", opacity: 0.8 }} />
        </div>

        {/* Role Explanation Card */}
        <div
          style={{
            background: tokens.colors.navyCardLight,
            borderLeft: `4px solid ${tokens.colors.yellowHighlight}`,
            borderRadius: 6,
            padding: "12px 16px",
          }}
        >
          <div style={{ color: tokens.colors.yellowHighlight, fontSize: 20, fontWeight: 900, textTransform: "uppercase" }}>
            {role_title}
          </div>
          <div style={{ color: tokens.colors.textOffWhite, fontSize: 18, marginTop: 2, lineHeight: 1.2 }}>
            {role_description}
          </div>
        </div>
      </div>
    </div>
  );
};
