import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface OutroPlateProps {
  masterLogoSrc?: string;
  tickerBaseSrc?: string;
}

export const OutroPlate: React.FC<OutroPlateProps> = ({
  masterLogoSrc,
  tickerBaseSrc,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Snappy broadcast spring entry
  const animProgress = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.6, stiffness: 130 },
  });

  const scale = 0.92 + animProgress * 0.08;
  const opacity = Math.min(animProgress * 1.5, 1);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "#030814",
        zIndex: 65,
        opacity,
        overflow: "hidden",
        fontFamily: "'Barlow Condensed', sans-serif",
      }}
    >
      {/* 1. Subtle Radial Studio Spotlight behind the logo */}
      <div
        style={{
          position: "absolute",
          top: "15%",
          left: "50%",
          transform: "translate(-50%, -20%)",
          width: 900,
          height: 900,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(20, 65, 170, 0.75) 0%, rgba(10, 35, 95, 0.35) 45%, transparent 72%)",
          pointerEvents: "none",
        }}
      />

      {/* 2. Angled Stadium Light Beams */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(115deg, transparent 40%, rgba(25, 80, 200, 0.08) 45%, transparent 50%), " +
            "linear-gradient(65deg, transparent 42%, rgba(25, 80, 200, 0.08) 47%, transparent 52%)",
          pointerEvents: "none",
        }}
      />

      {/* 3. Master 3D Bezel Logo (Centered Horizontally) */}
      <div
        style={{
          position: "absolute",
          top: 480,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${scale})`,
        }}
      >
        {masterLogoSrc ? (
          <img
            src={masterLogoSrc}
            alt="Channel Master Logo"
            style={{
              width: 720,
              height: "auto",
              objectFit: "contain",
              filter: "drop-shadow(0 14px 36px rgba(0, 0, 0, 0.9))",
            }}
          />
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div
              style={{
                background: "#D90429",
                color: "#FFFFFF",
                fontWeight: 900,
                fontSize: 72,
                padding: "10px 32px",
                borderRadius: 8,
                marginBottom: 16,
              }}
            >
              30s
            </div>
            <div
              style={{
                color: "#FFFFFF",
                fontWeight: 900,
                fontSize: 56,
                letterSpacing: "3px",
                textTransform: "uppercase",
              }}
            >
              FOOTBALL IN 30 SECONDS
            </div>
          </div>
        )}
      </div>

      {/* 4. Interactive Follow CTA Pill (Centered) */}
      <div
        style={{
          position: "absolute",
          top: 980,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${0.95 + animProgress * 0.05})`,
        }}
      >
        <div
          style={{
            width: 740,
            padding: "18px 0",
            textAlign: "center",
            background: "rgba(6, 18, 48, 0.94)",
            border: "2px solid #FFD700",
            borderRadius: 14,
            boxShadow:
              "0 0 28px rgba(255, 215, 0, 0.28), 0 8px 24px rgba(0, 0, 0, 0.8)",
          }}
        >
          <span
            style={{
              color: "#FFD700",
              fontWeight: 800,
              fontSize: 38,
              letterSpacing: "2.5px",
              textTransform: "uppercase",
            }}
          >
            FOLLOW FOR DAILY BREAKING NEWS
          </span>
        </div>
      </div>

      {/* 5. Sub-tagline below pill (Centered) */}
      <div
        style={{
          position: "absolute",
          top: 1090,
          left: 0,
          right: 0,
          textAlign: "center",
        }}
      >
        <span
          style={{
            color: "#A0C3F0",
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: "3px",
            textTransform: "uppercase",
          }}
        >
          DAILY TRANSFERS ● EXCLUSIVE SCOOPS ● BREAKING DRAMA
        </span>
      </div>

      {/* 6. Bottom 3D Ticker Base Plate */}
      {tickerBaseSrc ? (
        <img
          src={tickerBaseSrc}
          alt="Ticker Base"
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            width: 1080,
            height: "auto",
          }}
        />
      ) : (
        <div
          style={{
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            height: 190,
            background:
              "linear-gradient(180deg, #09122C 0%, #050B1B 60%, #000000 100%)",
            borderTop: "3px solid #D90429",
          }}
        />
      )}
    </div>
  );
};
