import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { tokens } from "../design/tokens";

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
  tickerText = "THIS IS FOOTBALL IN 30 SECONDS ✦ FOLLOW FOR MORE ✦ DAILY BREAKING NEWS ✦",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Step 2 & 3: Logo slides in smoothly from the RIGHT side (frames 0 to 14)
  const logoProgress = spring({
    frame,
    fps,
    config: { damping: 15, mass: 0.6, stiffness: 120 },
  });
  const logoTranslateX = (1 - logoProgress) * 450;
  const logoOpacity = Math.min(logoProgress * 1.5, 1);

  // Step 4: Tagline reveal (frames 10 to 22)
  const taglineProgress = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 120 },
  });
  const taglineTranslateY = (1 - taglineProgress) * 20;
  const taglineOpacity = Math.min(taglineProgress * 1.5, 1);

  // Step 5: Call To Action pill reveal (frames 18 to 30)
  const ctaProgress = spring({
    frame: Math.max(0, frame - 18),
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 130 },
  });
  const ctaScale = 0.94 + ctaProgress * 0.06;
  const ctaOpacity = Math.min(ctaProgress * 1.5, 1);

  const scrollOffset = (frame * 4.5) % 2400;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "#030814",
        zIndex: 65,
        overflow: "hidden",
        fontFamily: tokens.typography.fontDisplay,
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

      {/* 2. Authentic 90s Stadium Floodlight Beams */}
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

      {/* 4. Master 3D Bezel Logo (Slides in from RIGHT) */}
      <div
        style={{
          position: "absolute",
          top: 540,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `translateX(${logoTranslateX}px)`,
          opacity: logoOpacity,
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
              30+
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
              30 FOOTBALL PLUS
            </div>
          </div>
        )}
      </div>

      {/* 5. Tagline Reveal: THIS IS FOOTBALL IN 30 SECONDS */}
      <div
        style={{
          position: "absolute",
          top: 890,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `translateY(${taglineTranslateY}px)`,
          opacity: taglineOpacity,
        }}
      >
        <span
          style={{
            fontFamily: tokens.typography.fontDisplay,
            fontWeight: 900,
            fontSize: 48,
            color: "#FFFFFF",
            letterSpacing: "3px",
            textTransform: "uppercase",
            textShadow: "0 4px 16px rgba(0, 0, 0, 0.9)",
          }}
        >
          THIS IS FOOTBALL IN 30 SECONDS
        </span>
      </div>

      {/* 6. Call To Action Pill: FOLLOW FOR MORE */}
      <div
        style={{
          position: "absolute",
          top: 980,
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${ctaScale})`,
          opacity: ctaOpacity,
        }}
      >
        <div
          style={{
            width: 580,
            height: 72,
            background: "rgba(6, 18, 48, 0.95)",
            border: "2px solid #FFD700",
            borderRadius: 14,
            boxShadow:
              "0 0 32px rgba(255, 215, 0, 0.4), 0 8px 24px rgba(0, 0, 0, 0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
          }}
        >
          {/* Cyan edge highlight */}
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
              fontSize: 34,
              letterSpacing: "2.5px",
              textTransform: "uppercase",
              whiteSpace: "nowrap",
              textShadow: "0 2px 10px rgba(0, 0, 0, 0.9)",
            }}
          >
            FOLLOW FOR MORE
          </span>
        </div>
      </div>

      {/* 7. Subtle 1990s Scanline treatment over Outro */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "repeating-linear-gradient(0deg, rgba(0,0,0,0.12) 0px, rgba(0,0,0,0.12) 2px, transparent 2px, transparent 4px)",
          mixBlendMode: "multiply",
          pointerEvents: "none",
          opacity: 0.6,
        }}
      />
    </div>
  );
};
