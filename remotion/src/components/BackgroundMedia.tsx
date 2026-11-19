import React from "react";
import { Img, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneMotion } from "../types";

export interface BackgroundMediaProps {
  imagePath?: string;
  motion?: SceneMotion;
  durationInFrames: number;
}

export const BackgroundMedia: React.FC<BackgroundMediaProps> = ({
  imagePath,
  motion,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Subtle camera motion calculation
  let scale = 1.0;
  let translateX = 0;
  let translateY = 0;

  const motionType = motion?.type || "subtle_push_in";

  if (motionType === "subtle_push_in") {
    scale = interpolate(frame, [0, durationInFrames], [1.0, 1.08], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (motionType === "slow_pan") {
    scale = 1.06;
    translateX = interpolate(frame, [0, durationInFrames], [-20, 20], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (motionType === "pop_in") {
    const pop = spring({
      frame,
      fps,
      config: { damping: 14, mass: 0.6, stiffness: 120 },
    });
    scale = 0.94 + pop * 0.08;
  } else {
    scale = interpolate(frame, [0, durationInFrames], [1.02, 1.06], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  // Convert Windows backslashes to forward slashes for CSS / browser loading
  const normalizedPath = imagePath ? imagePath.replace(/\\/g, "/") : "";

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        backgroundColor: "#0B132B",
      }}
    >
      {/* Background Image with Camera Rig Transform */}
      {normalizedPath ? (
        <Img
          src={normalizedPath}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center 25%", // Prioritize face/upper body framing
            transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
            willChange: "transform",
          }}
        />
      ) : (
        <div
          style={{
            width: "100%",
            height: "100%",
            background: "linear-gradient(180deg, #1C2541 0%, #0B132B 100%)",
          }}
        />
      )}

      {/* Atmospheric Vignette & Text Contrast Gradients */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(11, 19, 43, 0.75) 0%, rgba(11, 19, 43, 0) 22%, rgba(11, 19, 43, 0.1) 60%, rgba(11, 19, 43, 0.95) 85%, #0B132B 100%)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
};
