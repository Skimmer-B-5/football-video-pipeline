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
      {/* 1. CRT Horizontal Scanlines (Subtle & Restrained) */}
      {enableScanlines && (
        scanlinesSrc ? (
          <img
            src={scanlinesSrc}
            alt="CRT Scanlines"
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              opacity: scanlineOpacity * flicker,
              mixBlendMode: "multiply",
            }}
          />
        ) : (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "repeating-linear-gradient(0deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 2px, transparent 2px, transparent 4px)",
              opacity: scanlineOpacity * flicker,
              mixBlendMode: "multiply",
            }}
          />
        )
      )}

      {/* 2. Authentic CRT Curved Screen Tube Vignette (No plastic frame) */}
      {enableVignette && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `radial-gradient(ellipse 85% 85% at 50% 50%, rgba(0, 0, 0, 0) 65%, rgba(0, 0, 0, ${vignetteIntensity * 0.85}) 96%, rgba(0, 0, 0, ${vignetteIntensity}) 100%)`,
            mixBlendMode: "multiply",
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
            height: 100,
            background:
              "linear-gradient(180deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0) 100%)",
            mixBlendMode: "screen",
          }}
        />
      )}
    </div>
  );
};
