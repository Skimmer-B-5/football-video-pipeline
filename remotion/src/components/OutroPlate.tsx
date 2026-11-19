import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface OutroPlateProps {
  masterLogoSrc?: string;
  tickerBaseSrc?: string;
  headlinesTabSrc?: string;
  tickerText?: string;
}

export const OutroPlate: React.FC<OutroPlateProps> = ({
  masterLogoSrc,
  tickerBaseSrc,
  headlinesTabSrc,
  tickerText = "FOLLOW FOR DAILY BREAKING NEWS ✦ EXCLUSIVE INTERVIEWS ✦ BREAKING TRANSFERS ✦",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Snappy broadcast spring entry
  const animProgress = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.6, stiffness: 130 },
  });

  const scale = 0.95 + animProgress * 0.05;
  const opacity = Math.min(animProgress * 1.5, 1);
  const scrollOffset = (frame * 4.5) % 2400;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "#030814",
        zIndex: 65,
        opacity,
        overflow: "hidden",
        fontFamily: "'Barlow Condensed', 'Arial Black', sans-serif",
      }}
    >
      {/* 1. Large Circular Stadium Spotlight Disc (x: 540, y: 700, radius: 600) */}
      <div
        style={{
          position: "absolute",
          top: 100,
          left: "50%",
          transform: "translateX(-50%)",
          width: 1200,
          height: 1200,
          borderRadius: "50%",
          background:
            "radial-gradient(circle at 50% 50%, rgba(20, 65, 175, 0.9) 0%, rgba(15, 45, 120, 0.7) 45%, rgba(8, 25, 75, 0.35) 75%, transparent 100%)",
          boxShadow: "0 0 180px rgba(20, 65, 175, 0.5)",
          pointerEvents: "none",
        }}
      />

      {/* 2. Authentic 90s Stadium Floodlight Beams (5 Angled Beams) */}
      <svg
        style={{
          position: "absolute",
          inset: 0,
          width: 1080,
          height: 1920,
          pointerEvents: "none",
        }}
      >
        {[-380, -190, 0, 190, 380].map((xOff, i) => {
          const spotX = 540;
          const p1 = `${spotX + xOff - 40},0`;
          const p2 = `${spotX + xOff + 40},0`;
          const p3 = `${spotX + Math.round(xOff * 1.8) + 120},1920`;
          const p4 = `${spotX + Math.round(xOff * 1.8) - 120},1920`;
          return (
            <polygon
              key={i}
              points={`${p1} ${p2} ${p3} ${p4}`}
              fill="rgba(35, 110, 245, 0.2)"
            />
          );
        })}
      </svg>

      {/* 3. Radial Vignette for Depth */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 90% 90% at 50% 50%, transparent 45%, rgba(3, 8, 20, 0.85) 85%, #030814 100%)",
          pointerEvents: "none",
        }}
      />

      {/* 4. Master 3D Bezel Logo (Centered Horizontally at y: 560) */}
      <div
        style={{
          position: "absolute",
          top: 560,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${scale})`,
          filter: "drop-shadow(0 18px 40px rgba(0, 0, 0, 0.95))",
        }}
      >
        {masterLogoSrc ? (
          <img
            src={masterLogoSrc}
            alt="30 Football Plus Master Logo"
            style={{
              width: 740,
              height: "auto",
              objectFit: "contain",
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

      {/* 5. Interactive Follow Card (Centered at y: 930, width: 680, height: 76) */}
      <div
        style={{
          position: "absolute",
          top: 930,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${0.96 + animProgress * 0.04})`,
        }}
      >
        <div
          style={{
            width: 680,
            height: 76,
            background: "rgba(6, 18, 48, 0.95)",
            border: "2px solid #FFD700",
            borderRadius: 14,
            boxShadow:
              "0 0 28px rgba(255, 215, 0, 0.35), 0 8px 24px rgba(0, 0, 0, 0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
          }}
        >
          {/* Subtle cyan specular edge highlight across top */}
          <div
            style={{
              position: "absolute",
              top: 2,
              left: 14,
              right: 14,
              height: 1,
              background: "rgba(120, 190, 255, 0.7)",
            }}
          />
          <span
            style={{
              color: "#FFD700",
              fontWeight: 900,
              fontSize: 30,
              letterSpacing: "1.5px",
              textTransform: "uppercase",
              whiteSpace: "nowrap",
              textShadow: "0 2px 8px rgba(0, 0, 0, 0.8)",
            }}
          >
            FOLLOW FOR DAILY BREAKING NEWS
          </span>
        </div>
      </div>

      {/* 6. Sub-tagline below pill (Centered at y: 1038) */}
      <div
        style={{
          position: "absolute",
          top: 1038,
          left: 0,
          right: 0,
          textAlign: "center",
        }}
      >
        <span
          style={{
            color: "#A0C3F0",
            fontWeight: 800,
            fontSize: 22,
            letterSpacing: "2.5px",
            textTransform: "uppercase",
          }}
        >
          DAILY TRANSFERS &nbsp;✦&nbsp; EXCLUSIVE SCOOPS &nbsp;✦&nbsp; BREAKING DRAMA
        </span>
      </div>

      {/* 7. Bottom 3D Ticker Base Plate with Red HEADLINES Tab */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 110,
          overflow: "hidden",
          borderTop: "2px solid rgba(255, 209, 102, 0.45)",
          boxShadow: "0 -6px 20px rgba(0, 0, 0, 0.8)",
        }}
      >
        {/* 3D Ticker Base Plate */}
        {tickerBaseSrc ? (
          <img
            src={tickerBaseSrc}
            alt="Ticker Base"
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              width: 1080,
              height: 110,
              objectFit: "cover",
            }}
          />
        ) : (
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: 110,
              background: "linear-gradient(180deg, #09122C 0%, #050B1B 60%, #000000 100%)",
              borderTop: "3px solid #D90429",
            }}
          />
        )}

        {/* 3D Red Headlines Tab on Left */}
        {headlinesTabSrc ? (
          <img
            src={headlinesTabSrc}
            alt="Headlines"
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              width: 280,
              height: 110,
              zIndex: 5,
            }}
          />
        ) : (
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              width: 260,
              height: 110,
              background: "#D90429",
              color: "#FFFFFF",
              fontWeight: 900,
              fontSize: 26,
              letterSpacing: "2px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 5,
              boxShadow: "4px 0 14px rgba(0, 0, 0, 0.6)",
            }}
          >
            HEADLINES
          </div>
        )}

        {/* Rolling Ticker Text on Base */}
        <div
          style={{
            position: "absolute",
            left: 280,
            right: 0,
            bottom: 0,
            height: 110,
            overflow: "hidden",
            display: "flex",
            alignItems: "center",
            zIndex: 3,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 800 - scrollOffset,
              whiteSpace: "nowrap",
              color: "#FFFFFF",
              fontWeight: 800,
              fontSize: 26,
              letterSpacing: "1.5px",
              textTransform: "uppercase",
            }}
          >
            {tickerText} &nbsp;&nbsp;✦&nbsp;&nbsp; {tickerText}
          </div>
        </div>
      </div>
    </div>
  );
};
