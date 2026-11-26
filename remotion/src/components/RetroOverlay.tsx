import React from "react";
import { useCurrentFrame } from "remotion";
import { tokens } from "../design/tokens";

export interface RetroOverlayProps {
  scanlinesSrc?: string;
  enableScanlines?: boolean;
  enableVignette?: boolean;
  enableFlicker?: boolean;
  scanlineOpacity?: number;
  vignetteIntensity?: number;
}

export const RetroOverlay: React.FC<RetroOverlayProps> = ({
  scanlinesSrc,
  enableScanlines = true,
  enableVignette = true,
  enableFlicker = true,
  scanlineOpacity = tokens.crt.scanlineOpacity,
  vignetteIntensity = tokens.crt.vignetteIntensity,
}) => {
  const frame = useCurrentFrame();

  // Subtle analog CRT phosphor shimmer (restrained 1.5% fluctuation)
  const flicker = enableFlicker ? Math.sin(frame * 0.45) * tokens.crt.flickerDepth + (1 - tokens.crt.flickerDepth) : 1.0;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        zIndex: tokens.layout.crtOverlay.zIndex,
        overflow: "hidden",
      }}
    >
      {/* 1. CRT Horizontal Scanlines & Phosphor Aperture Grille */}
      {enableScanlines && (
        <>
          {/* Authentic Trinitron Horizontal Scanlines */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.18) 50%)",
              backgroundSize: "100% 4px",
              opacity: 0.65 * flicker,
              mixBlendMode: "multiply",
              pointerEvents: "none",
            }}
          />
          {/* Subtle Trinitron Vertical Phosphor Aperture Grille (RGB sub-pixels) */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "repeating-linear-gradient(90deg, rgba(255, 0, 0, 0.03) 0px, rgba(0, 255, 0, 0.02) 1px, rgba(0, 0, 255, 0.03) 2px, transparent 3px)",
              backgroundSize: "3px 100%",
              opacity: 0.75,
              mixBlendMode: "screen",
              pointerEvents: "none",
            }}
          />
        </>
      )}

      {/* 2. Authentic CRT Curved Screen Tube Vignette */}
      {enableVignette && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(ellipse 80% 80% at 50% 50%, rgba(0, 0, 0, 0) 55%, rgba(0, 0, 0, 0.35) 85%, rgba(0, 0, 0, 0.75) 100%)",
            mixBlendMode: "multiply",
            pointerEvents: "none",
          }}
        />
      )}

      {/* 3. Subtle Glass Reflection Highlight along top tube bevel */}
      {tokens.crt.tubeEdgeReflection && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 140,
            background:
              "linear-gradient(180deg, rgba(255, 255, 255, 0.07) 0%, rgba(255, 255, 255, 0.02) 40%, rgba(255, 255, 255, 0) 100%)",
            mixBlendMode: "screen",
            pointerEvents: "none",
          }}
        />
      )}
    </div>
  );
};
