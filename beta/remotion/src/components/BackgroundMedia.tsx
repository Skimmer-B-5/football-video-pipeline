import React from "react";
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneMotion, SceneShot } from "../types";

export interface BackgroundMediaProps {
  imagePath?: string;
  shots?: SceneShot[];
  motion?: SceneMotion;
  durationInFrames: number;
}

export const BackgroundMedia: React.FC<BackgroundMediaProps> = ({
  imagePath,
  shots,
  motion,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Multi-shot editorial rhythm resolution
  let activeImagePath = imagePath;
  let activeFrame = frame;
  let activeDuration = durationInFrames;

  if (shots && shots.length > 0) {
    let acc = 0;
    for (let i = 0; i < shots.length; i++) {
      const s = shots[i];
      if (frame >= acc && frame < acc + s.durationInFrames) {
        activeImagePath = s.image_path;
        activeFrame = frame - acc;
        activeDuration = s.durationInFrames;
        break;
      }
      acc += s.durationInFrames;
    }
    if (frame >= acc) {
      const lastShot = shots[shots.length - 1];
      activeImagePath = lastShot.image_path;
      activeFrame = frame - (acc - lastShot.durationInFrames);
      activeDuration = lastShot.durationInFrames;
    }
  }

  // Subtle camera motion calculation
  let scale = 1.0;
  let translateX = 0;
  let translateY = 0;

  const motionType = motion?.type || "subtle_push_in";

  if (motionType === "subtle_push_in") {
    scale = interpolate(activeFrame, [0, activeDuration], [1.0, 1.08], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (motionType === "slow_pan") {
    scale = 1.06;
    translateX = interpolate(activeFrame, [0, activeDuration], [-20, 20], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (motionType === "pop_in") {
    const pop = spring({
      frame: activeFrame,
      fps,
      config: { damping: 14, mass: 0.6, stiffness: 120 },
    });
    scale = 0.94 + pop * 0.08;
  } else {
    scale = interpolate(activeFrame, [0, activeDuration], [1.02, 1.06], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  // Convert Windows backslashes to forward slashes and resolve via staticFile for fast local serving
  const normalizedPath = activeImagePath ? activeImagePath.replace(/\\/g, "/") : "";
  let resolvedSrc = normalizedPath;
  if (normalizedPath && !normalizedPath.startsWith("data:") && !normalizedPath.startsWith("http")) {
    const cleanRel = normalizedPath.replace(/^\//, "");
    try {
      resolvedSrc = staticFile(cleanRel);
    } catch {
      resolvedSrc = "/" + cleanRel;
    }
  }

  // Section 5: Consistent 8-frame broadcast directional sweep / wipe transition
  const wipeFrames = 8;
  const isTransitioning = activeFrame < wipeFrames;
  const wipeProgress = interpolate(activeFrame, [0, wipeFrames], [0.0, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const wipePercent = wipeProgress * 100;
  
  // Section 2: Authentic 1990s CRT Broadcast Characteristics
  // 1. Very subtle horizontal signal sync jitter (sub-pixel line instability)
  const syncJitterX = Math.sin(frame * 2.1) * 0.75;
  const currentTranslateX = isTransitioning ? (1 - wipeProgress) * -35 : translateX + syncJitterX;

  // 2. Gentle cathode phosphor shimmer
  const phosphorFlicker = Math.sin(frame * 0.45) * 0.015 + 0.985;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        backgroundColor: "#0B132B",
      }}
    >
      {/* 1. Primary Background Image with CRT Analog Color Grade & Softening */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: isTransitioning
            ? `polygon(0 0, ${wipePercent}% 0, ${wipePercent}% 100%, 0 100%)`
            : undefined,
        }}
      >
        {resolvedSrc ? (
          <>
            {/* Base Image with CRT Analog Grade (Slightly Softened, Rich Contrast, Warm Midtones) */}
            <Img
              src={resolvedSrc}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "center 25%", // Prioritize face/upper body framing
                transform: `scale(${scale}) translate(${currentTranslateX}px, ${translateY}px)`,
                filter: "contrast(1.08) brightness(0.98) saturate(1.16) blur(0.5px)",
                willChange: "transform",
              }}
            />

            {/* Phosphor Glow / Bloom on Highlights (Screen Blend) */}
            <Img
              src={resolvedSrc}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "center 25%",
                transform: `scale(${scale}) translate(${currentTranslateX}px, ${translateY}px)`,
                filter: "blur(14px) brightness(1.3) saturate(1.2)",
                opacity: 0.32,
                mixBlendMode: "screen",
                pointerEvents: "none",
              }}
            />

            {/* Subtle RGB Chromatic Separation (Trinitron Aperture Grille Fringing) */}
            <Img
              src={resolvedSrc}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "center 25%",
                transform: `scale(${scale}) translate(${currentTranslateX - 2.2}px, ${translateY}px)`,
                filter: "hue-rotate(-25deg) saturate(1.4) blur(0.4px)",
                opacity: 0.16,
                mixBlendMode: "screen",
                pointerEvents: "none",
              }}
            />
            <Img
              src={resolvedSrc}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "center 25%",
                transform: `scale(${scale}) translate(${currentTranslateX + 2.2}px, ${translateY}px)`,
                filter: "hue-rotate(170deg) saturate(1.4) blur(0.4px)",
                opacity: 0.16,
                mixBlendMode: "screen",
                pointerEvents: "none",
              }}
            />
          </>
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              background: "linear-gradient(180deg, #1C2541 0%, #0B132B 100%)",
            }}
          />
        )}
      </div>

      {/* 2. 8-Frame Directional Broadcast Wipe Highlight Bar */}
      {isTransitioning && (
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: `${wipePercent}%`,
            width: 4,
            background:
              "linear-gradient(180deg, rgba(255, 215, 0, 0.9) 0%, rgba(56, 189, 248, 0.9) 50%, rgba(255, 255, 255, 0.9) 100%)",
            boxShadow:
              "0 0 14px rgba(56, 189, 248, 0.8), -3px 0 12px rgba(255, 215, 0, 0.4)",
            zIndex: 4,
            pointerEvents: "none",
          }}
        />
      )}

      {/* 3. Clearly Visible 1990s CRT Horizontal Scanlines (Recognisable on Mobile Phones) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "repeating-linear-gradient(0deg, rgba(0, 0, 0, 0.42) 0px, rgba(0, 0, 0, 0.42) 2px, transparent 2px, transparent 4px)",
          mixBlendMode: "multiply",
          pointerEvents: "none",
          opacity: 0.88 * phosphorFlicker,
          zIndex: 3,
        }}
      />

      {/* 4. Subtle Analog Signal Noise / Micro RF Grain */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.03) 0%, rgba(0, 0, 0, 0.12) 100%)",
          mixBlendMode: "overlay",
          pointerEvents: "none",
          opacity: 0.75,
          zIndex: 3,
        }}
      />

      {/* 5. Atmospheric Vignette & Text Contrast Gradients */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(11, 19, 43, 0.75) 0%, rgba(11, 19, 43, 0) 22%, rgba(11, 19, 43, 0.1) 60%, rgba(11, 19, 43, 0.95) 85%, #0B132B 100%)",
          pointerEvents: "none",
          zIndex: 2,
        }}
      />
    </div>
  );
};
