import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export const ContractExplainer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Staggered spring animations for boxes and arrows
  const cardSpring = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.6, stiffness: 110 },
  });

  const arrowSpring = spring({
    frame: frame - 8,
    fps,
    config: { damping: 12, mass: 0.5, stiffness: 130 },
  });

  const returnSpring = spring({
    frame: frame - 16,
    fps,
    config: { damping: 12, mass: 0.5, stiffness: 130 },
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 35,
        padding: "0 90px",
      }}
    >
      {/* Background Dimmer Card */}
      <div
        style={{
          width: "100%",
          background: "rgba(11, 19, 43, 0.95)",
          border: "2px solid rgba(255, 209, 102, 0.3)",
          borderRadius: 16,
          padding: "36px 30px",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.8)",
          transform: `scale(${0.9 + cardSpring * 0.1})`,
          opacity: Math.min(cardSpring, 1),
        }}
      >
        <div
          style={{
            textAlign: "center",
            color: "#FFD166",
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 800,
            fontSize: 28,
            letterSpacing: "3px",
            textTransform: "uppercase",
            marginBottom: 24,
            borderBottom: "1px solid rgba(255, 209, 102, 0.2)",
            paddingBottom: 12,
          }}
        >
          REPORTED DEAL MECHANICS
        </div>

        {/* Club Row */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 28,
          }}
        >
          {/* Real Madrid */}
          <div
            style={{
              flex: 1,
              background: "#1C2541",
              border: "2px solid #FFFFFF",
              borderRadius: 8,
              padding: "16px 12px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                color: "#FFFFFF",
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 900,
                fontSize: 32,
                textTransform: "uppercase",
              }}
            >
              REAL MADRID
            </div>
            <div style={{ color: "#A0AAB2", fontSize: 20 }}>Seller Club</div>
          </div>

          {/* Central VS / Arrow Indicator */}
          <div
            style={{
              margin: "0 16px",
              color: "#FFD166",
              fontWeight: 900,
              fontSize: 28,
            }}
          >
            ➔
          </div>

          {/* AC Milan */}
          <div
            style={{
              flex: 1,
              background: "#1C2541",
              border: "2px solid #D90429",
              borderRadius: 8,
              padding: "16px 12px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                color: "#D90429",
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 900,
                fontSize: 32,
                textTransform: "uppercase",
              }}
            >
              AC MILAN
            </div>
            <div style={{ color: "#A0AAB2", fontSize: 20 }}>Bidding Club</div>
          </div>
        </div>

        {/* Transfer Fee Card (Madrid -> Milan) */}
        <div
          style={{
            background: "linear-gradient(90deg, #1C2541 0%, #2A3B66 100%)",
            borderLeft: "6px solid #FFD166",
            borderRadius: 6,
            padding: "16px 20px",
            marginBottom: 16,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            transform: `translateY(${(1 - Math.min(arrowSpring, 1)) * 20}px)`,
            opacity: Math.min(arrowSpring, 1),
          }}
        >
          <div>
            <div
              style={{
                color: "#FFFFFF",
                fontWeight: 800,
                fontSize: 26,
                textTransform: "uppercase",
              }}
            >
              Transfer Package
            </div>
            <div style={{ color: "#FFD166", fontSize: 20 }}>
              Winter 2025 Proposed Bid
            </div>
          </div>
          <div
            style={{
              color: "#FFD166",
              fontFamily: "'Barlow Condensed', sans-serif",
              fontWeight: 900,
              fontSize: 44,
              letterSpacing: "1px",
            }}
          >
            €60M + €10M
          </div>
        </div>

        {/* Buy-Back Clause Card (Milan -> Madrid) */}
        <div
          style={{
            background: "linear-gradient(90deg, #1C2541 0%, #173753 100%)",
            borderLeft: "6px solid #48CAE4",
            borderRadius: 6,
            padding: "16px 20px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            transform: `translateY(${(1 - Math.min(returnSpring, 1)) * 20}px)`,
            opacity: Math.min(returnSpring, 1),
          }}
        >
          <div>
            <div
              style={{
                color: "#FFFFFF",
                fontWeight: 800,
                fontSize: 26,
                textTransform: "uppercase",
              }}
            >
              Return Option (Nico Paz Model)
            </div>
            <div style={{ color: "#48CAE4", fontSize: 20 }}>
              Madrid Buy-Back Clause
            </div>
          </div>
          <div
            style={{
              color: "#48CAE4",
              fontFamily: "'Barlow Condensed', sans-serif",
              fontWeight: 900,
              fontSize: 44,
              letterSpacing: "1px",
            }}
          >
            €80M
          </div>
        </div>
      </div>
    </div>
  );
};
