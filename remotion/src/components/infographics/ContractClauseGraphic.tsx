import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../../design/tokens";

export interface ContractClauseGraphicProps {
  selling_club?: string;
  buying_club?: string;
  package_fee?: string;
  clause_type?: string;
  clause_value?: string;
  terms?: string;
}

export const ContractClauseGraphic: React.FC<ContractClauseGraphicProps> = ({
  selling_club = "SELLING CLUB",
  buying_club = "BUYING CLUB",
  package_fee = "€60M + €10M",
  clause_type = "BUY-BACK CLAUSE",
  clause_value = "€80M",
  terms = "Valid Summer 2026 / 2027",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardEntrance = spring({
    frame,
    fps,
    config: tokens.animation.springSmooth,
  });

  const clauseEntrance = spring({
    frame: frame - 8,
    fps,
    config: tokens.animation.springBrisk,
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
          borderRadius: 14,
          padding: "26px 24px",
          boxShadow: tokens.colors.shadowHeavy,
          transform: `scale(${0.92 + cardEntrance * 0.08})`,
          opacity: Math.min(cardEntrance * 1.5, 1),
          fontFamily: tokens.typography.fontPrimary,
        }}
      >
        {/* Header */}
        <div
          style={{
            textAlign: "center",
            color: tokens.colors.yellowHighlight,
            fontSize: tokens.typography.sizes.infographicTitle,
            fontWeight: tokens.typography.weights.black,
            letterSpacing: tokens.typography.letterSpacing.wide,
            textTransform: "uppercase",
            marginBottom: 20,
            borderBottom: "1px solid rgba(255, 209, 102, 0.25)",
            paddingBottom: 10,
          }}
        >
          CONTRACTUAL CLAUSE MECHANICS
        </div>

        {/* Clubs Interaction Bar */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          {/* Selling Club */}
          <div
            style={{
              flex: 1,
              background: tokens.colors.navyCardLight,
              border: "1px solid rgba(255, 255, 255, 0.2)",
              borderRadius: 8,
              padding: "14px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ color: tokens.colors.textWhite, fontSize: 26, fontWeight: 900, textTransform: "uppercase" }}>
              {selling_club}
            </div>
            <div style={{ color: tokens.colors.textMuted, fontSize: 16 }}>Seller Option</div>
          </div>

          <div
            style={{
              margin: "0 14px",
              color: tokens.colors.yellowHighlight,
              fontWeight: 900,
              fontSize: 26,
            }}
          >
            ⇄
          </div>

          {/* Buying Club */}
          <div
            style={{
              flex: 1,
              background: tokens.colors.navyCardLight,
              border: `1px solid ${tokens.colors.redNews}`,
              borderRadius: 8,
              padding: "14px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ color: tokens.colors.cyanTactical, fontSize: 26, fontWeight: 900, textTransform: "uppercase" }}>
              {buying_club}
            </div>
            <div style={{ color: tokens.colors.textMuted, fontSize: 16 }}>Holder Club</div>
          </div>
        </div>

        {/* Outgoing Transfer Package */}
        <div
          style={{
            background: "linear-gradient(90deg, #1C2541 0%, #2A3B66 100%)",
            borderLeft: `6px solid ${tokens.colors.yellowHighlight}`,
            borderRadius: 8,
            padding: "14px 18px",
            marginBottom: 14,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <div style={{ color: tokens.colors.textWhite, fontWeight: 800, fontSize: 22, textTransform: "uppercase" }}>
              Initial Transfer Package
            </div>
            <div style={{ color: tokens.colors.yellowHighlight, fontSize: 16 }}>Agreed Outgoing Fee</div>
          </div>
          <div
            style={{
              color: tokens.colors.yellowHighlight,
              fontSize: 38,
              fontWeight: 900,
              letterSpacing: "1px",
            }}
          >
            {package_fee}
          </div>
        </div>

        {/* Clause Mechanism (Buy-back / Sell-on / Release) */}
        <div
          style={{
            background: "linear-gradient(90deg, #1C2541 0%, #153A52 100%)",
            borderLeft: `6px solid ${tokens.colors.cyanTactical}`,
            borderRadius: 8,
            padding: "14px 18px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            transform: `translateY(${(1 - Math.min(clauseEntrance, 1)) * 15}px)`,
            opacity: Math.min(clauseEntrance, 1),
          }}
        >
          <div>
            <div style={{ color: tokens.colors.textWhite, fontWeight: 800, fontSize: 22, textTransform: "uppercase" }}>
              {clause_type}
            </div>
            <div style={{ color: tokens.colors.cyanTactical, fontSize: 16 }}>{terms}</div>
          </div>
          <div
            style={{
              color: tokens.colors.cyanTactical,
              fontSize: 38,
              fontWeight: 900,
              letterSpacing: "1px",
            }}
          >
            {clause_value}
          </div>
        </div>
      </div>
    </div>
  );
};
