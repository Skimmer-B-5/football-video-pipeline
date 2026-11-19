import React from "react";
import { useCurrentFrame } from "remotion";

export interface RetroOverlayProps {
  scanlinesSrc?: string;
  enableScanlines?: boolean;
  enableVignette?: boolean;
  enableFlicker?: boolean;
}

export const RetroOverlay: React.FC<RetroOverlayProps> = ({
  scanlinesSrc,
  enableScanlines = true,
  enableVignette = true,
  enableFlicker = true,
}) => {
  const frame = useCurrentFrame();

  // Subtle analog CRT phosphor shimmer (imperceptible 1-2% fluctuation)
  const flicker = enableFlicker ? Math.sin(frame * 0.45) * 0.02 + 0.98 : 1.0;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        zIndex: 75,
        overflow: "hidden",
      }}
    >
      {/* 1. CRT Scanlines Overlay Texture */}
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
              opacity: 0.52 * flicker,
              mixBlendMode: "multiply",
            }}
          />
        ) : (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "repeating-linear-gradient(0deg, rgba(0,0,0,0.22) 0px, rgba(0,0,0,0.22) 2px, transparent 2px, transparent 4px)",
              opacity: 0.7 * flicker,
              mixBlendMode: "multiply",
            }}
          />
        )
      )}

      {/* 2. Authentic CRT Curved Screen Vignette */}
      {enableVignette && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "radial-gradient(ellipse 85% 85% at 50% 50%, rgba(0, 0, 0, 0) 60%, rgba(0, 0, 0, 0.48) 95%, rgba(0, 0, 0, 0.8) 100%)",
            mixBlendMode: "multiply",
          }}
        />
      )}

      {/* 3. Subtle TV Glass Reflection / Tube Edge Highlight */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 120,
          background:
            "linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0) 100%)",
          mixBlendMode: "screen",
        }}
      />
    </div>
  );
};
