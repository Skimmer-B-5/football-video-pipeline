import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface TransferFeeGraphicProps {
  guaranteed?: string;
  add_ons?: string;
  total_package?: string;
  selling_club?: string;
  buying_club?: string;
  structure?: string;
}

export const TransferFeeGraphic: React.FC<TransferFeeGraphicProps> = ({
  guaranteed = "€60M",
  add_ons = "€10M",
  total_package = "€70M TOTAL",
  selling_club = "SELLING CLUB",
  buying_club = "BUYING CLUB",
  structure = "Fixed Base + Performance Add-ons",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardEntrance = spring({
    frame,
    fps,
    config: tokens.animation.springSmooth,
  });

  const valueEntrance = spring({
    frame: frame - 6,
    fps,
    config: tokens.animation.springBrisk,
  });

  return (
    <div
      style={{
        position: "absolute",
        top: tokens.layout.stage.top + 20,
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
          padding: "28px 24px",
          boxShadow: tokens.colors.shadowHeavy,
          transform: `scale(${0.92 + cardEntrance * 0.08})`,
          opacity: Math.min(cardEntrance * 1.5, 1),
          fontFamily: tokens.typography.fontPrimary,
        }}
      >
        {/* Header Ribbon */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid rgba(255, 209, 102, 0.25)",
            paddingBottom: 12,
            marginBottom: 20,
          }}
        >
          <span
            style={{
              color: tokens.colors.yellowHighlight,
              fontSize: tokens.typography.sizes.infographicTitle,
              fontWeight: tokens.typography.weights.black,
              letterSpacing: tokens.typography.letterSpacing.wide,
              textTransform: "uppercase",
            }}
          >
            TRANSFER FINANCIAL VALUATION
          </span>
          <span
            style={{
              background: tokens.colors.redNews,
              color: tokens.colors.textWhite,
              fontSize: tokens.typography.sizes.dataCallout,
              fontWeight: tokens.typography.weights.black,
              padding: "4px 12px",
              borderRadius: 4,
              letterSpacing: tokens.typography.letterSpacing.normal,
            }}
          >
            FEE BREAKDOWN
          </span>
        </div>

        {/* Club Exchange Headers */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: tokens.colors.navyCardLight,
            borderRadius: 8,
            padding: "14px 18px",
            marginBottom: 20,
          }}
        >
          <div style={{ textAlign: "left" }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: 18, textTransform: "uppercase" }}>From</div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 26, fontWeight: 900 }}>{selling_club}</div>
          </div>
          <div style={{ color: tokens.colors.yellowHighlight, fontSize: 30, fontWeight: 900 }}>➔</div>
          <div style={{ textAlign: "right" }}>
            <div style={{ color: tokens.colors.textMuted, fontSize: 18, textTransform: "uppercase" }}>To</div>
            <div style={{ color: tokens.colors.cyanTactical, fontSize: 26, fontWeight: 900 }}>{buying_club}</div>
          </div>
        </div>

        {/* Guaranteed & Add-Ons 2-Column Split */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 16,
            marginBottom: 20,
            transform: `translateY(${(1 - Math.min(valueEntrance, 1)) * 15}px)`,
            opacity: Math.min(valueEntrance, 1),
          }}
        >
          {/* Guaranteed Fee */}
          <div
            style={{
              background: "linear-gradient(180deg, #1C2541 0%, #151E38 100%)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: 8,
              padding: "16px",
              textAlign: "center",
            }}
          >
            <div style={{ color: tokens.colors.textMuted, fontSize: 18, fontWeight: 700, textTransform: "uppercase" }}>
              Guaranteed Base
            </div>
            <div
              style={{
                color: tokens.colors.textWhite,
                fontSize: 48,
                fontWeight: 900,
                marginTop: 4,
                letterSpacing: "1px",
              }}
            >
              {guaranteed}
            </div>
          </div>

          {/* Add-ons Fee */}
          <div
            style={{
              background: "linear-gradient(180deg, #1C2541 0%, #151E38 100%)",
              border: `1px solid ${tokens.colors.yellowSubtle}`,
              borderRadius: 8,
              padding: "16px",
              textAlign: "center",
            }}
          >
            <div style={{ color: tokens.colors.yellowHighlight, fontSize: 18, fontWeight: 700, textTransform: "uppercase" }}>
              Performance Bonus
            </div>
            <div
              style={{
                color: tokens.colors.yellowHighlight,
                fontSize: 48,
                fontWeight: 900,
                marginTop: 4,
                letterSpacing: "1px",
              }}
            >
              {add_ons}
            </div>
          </div>
        </div>

        {/* Total Package Banner */}
        <div
          style={{
            background: "linear-gradient(90deg, #9B0014 0%, #D90429 100%)",
            borderRadius: 8,
            padding: "14px 20px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            boxShadow: tokens.colors.shadowGlowRed,
          }}
        >
          <div>
            <div style={{ color: tokens.colors.textWhite, fontSize: 20, fontWeight: 800, textTransform: "uppercase" }}>
              Total Valuation
            </div>
            <div style={{ color: "rgba(255, 255, 255, 0.8)", fontSize: 16 }}>{structure}</div>
          </div>
          <div
            style={{
              color: tokens.colors.textWhite,
              fontSize: 42,
              fontWeight: 900,
              letterSpacing: "1.5px",
            }}
          >
            {total_package}
          </div>
        </div>
      </div>
    </div>
  );
};
