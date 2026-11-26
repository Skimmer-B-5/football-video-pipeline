import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface TransferRouteGraphicProps {
  selling_club?: string;
  buying_club?: string;
  player_name?: string;
  transfer_status?: string;
  fee?: string;
}

export const TransferRouteGraphic: React.FC<TransferRouteGraphicProps> = ({
  selling_club = "CURRENT CLUB",
  buying_club = "DESTINATION CLUB",
  player_name = "TARGET PLAYER",
  transfer_status = "ADVANCED TALKS",
  fee = "€55M PACKAGE",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: tokens.animation.springSmooth,
  });

  const arrowPulse = Math.sin(frame * 0.2) * 6;

  return (
    <div
      style={{
        position: "absolute",
        top: tokens.layout.stage.top + 15,
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
          padding: "26px 24px",
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
            paddingBottom: 10,
            marginBottom: 20,
          }}
        >
          <div>
            <div style={{ color: tokens.colors.textMuted, fontSize: 16, textTransform: "uppercase" }}>
              TRANSFER ROUTE TRACKER
            </div>
            <div
              style={{
                color: tokens.colors.yellowHighlight,
                fontSize: 32,
                fontWeight: 900,
                textTransform: "uppercase",
              }}
            >
              {player_name}
            </div>
          </div>
          <span
            style={{
              background:
                transfer_status === "OFFICIAL"
                  ? tokens.colors.greenOfficial
                  : transfer_status === "RUMOUR"
                  ? tokens.colors.amberRumour
                  : tokens.colors.redNews,
              color: tokens.colors.textWhite,
              fontSize: 18,
              fontWeight: 900,
              padding: "4px 12px",
              borderRadius: 4,
              letterSpacing: "1px",
              textTransform: "uppercase",
            }}
          >
            {transfer_status}
          </span>
        </div>

        {/* Vertical Step-by-Step Route */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Departure Card */}
          <div
            style={{
              background: tokens.colors.navyCardLight,
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: 8,
              padding: "16px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <span style={{ color: tokens.colors.redNews, fontSize: 16, fontWeight: 900, textTransform: "uppercase" }}>
                ORIGIN CLUB
              </span>
              <div style={{ color: tokens.colors.textWhite, fontSize: 32, fontWeight: 900, textTransform: "uppercase" }}>
                {selling_club}
              </div>
            </div>
            <div style={{ color: tokens.colors.textMuted, fontSize: 20, fontWeight: 700 }}>DEPARTING</div>
          </div>

          {/* Directional Route Indicator */}
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: 16,
              transform: `translateY(${arrowPulse}px)`,
            }}
          >
            <div style={{ height: 2, flex: 1, background: "rgba(255, 209, 102, 0.3)" }} />
            <div
              style={{
                background: tokens.colors.yellowHighlight,
                color: tokens.colors.navyPrimary,
                fontSize: 20,
                fontWeight: 900,
                padding: "4px 16px",
                borderRadius: 20,
                letterSpacing: "1px",
              }}
            >
              ▼ {fee} ▼
            </div>
            <div style={{ height: 2, flex: 1, background: "rgba(255, 209, 102, 0.3)" }} />
          </div>

          {/* Destination Card */}
          <div
            style={{
              background: "linear-gradient(90deg, #1C2541 0%, #1B3B6F 100%)",
              border: `2px solid ${tokens.colors.cyanTactical}`,
              borderRadius: 8,
              padding: "16px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              boxShadow: "0 4px 16px rgba(72, 202, 228, 0.25)",
            }}
          >
            <div>
              <span style={{ color: tokens.colors.cyanTactical, fontSize: 16, fontWeight: 900, textTransform: "uppercase" }}>
                DESTINATION CLUB
              </span>
              <div style={{ color: tokens.colors.textWhite, fontSize: 32, fontWeight: 900, textTransform: "uppercase" }}>
                {buying_club}
              </div>
            </div>
            <div style={{ color: tokens.colors.yellowHighlight, fontSize: 20, fontWeight: 800 }}>ARRIVAL</div>
          </div>
        </div>
      </div>
    </div>
  );
};
