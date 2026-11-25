import React from "react";
import { Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneMotion, SceneShot, SceneTransitionIn } from "../types";

export interface BackgroundMediaProps {
  imagePath?: string;
  shots?: SceneShot[];
  motion?: SceneMotion;
  transitionIn?: SceneTransitionIn;
  durationInFrames: number;
}

function resolveImgSrc(rawPath?: string): string {
  const normalizedPath = rawPath ? rawPath.replace(/\\/g, "/") : "";
  if (!normalizedPath) return "";
  if (normalizedPath.startsWith("data:") || normalizedPath.startsWith("http")) {
    return normalizedPath;
  }
  const cleanRel = normalizedPath.replace(/^\//, "");
  try {
    return staticFile(cleanRel);
  } catch {
    return "/" + cleanRel;
  }
}

export const BackgroundMedia: React.FC<BackgroundMediaProps> = ({
  imagePath,
  shots,
  motion,
  transitionIn,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const motionType = motion?.type || "subtle_push_in";
  const isSplitDuel = motionType === "split_duel" && shots && shots.length >= 2;

  // Dual-choice animated split-duel faceoff on S07 when 2 verified shots exist
  if (isSplitDuel && shots) {
    const s1 = shots[0];
    const s2 = shots[1];
    const src1 = resolveImgSrc(s1.image_path);
    const src2 = resolveImgSrc(s2.image_path);
    const fx1 = s1.focal_x ?? 50;
    const fy1 = s1.focal_y ?? 25;
    const fx2 = s2.focal_x ?? 50;
    const fy2 = s2.focal_y ?? 25;

    const splitStart = Math.max(12, Math.floor(s1.durationInFrames * 0.72));
    const splitEnd = Math.min(durationInFrames - 10, splitStart + 11);
    const splitProgress = interpolate(frame, [splitStart, splitEnd], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.22, 1, 0.36, 1),
    });

    const leftWidthPct = interpolate(splitProgress, [0, 1], [100, 50]);
    const rightTranslateXPct = interpolate(splitProgress, [0, 1], [100, 0]);
    const dividerOpacity = interpolate(splitProgress, [0, 0.2, 1], [0, 1, 1]);
    const zoom1 = interpolate(frame, [0, durationInFrames], [1.0, 1.06], { extrapolateRight: "clamp" });
    const zoom2 = interpolate(frame, [splitStart, durationInFrames], [1.06, 1.0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

    // Subtle scene-entry whip-pan offset on initial entry
    const entryEase = interpolate(frame, [0, 8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.22, 1, 0.36, 1),
    });
    const entryOffsetX = (1 - entryEase) * 65;

    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          overflow: "hidden",
          backgroundColor: "#0B132B",
          transform: `translateX(${entryOffsetX}px)`,
        }}
      >
        {/* Left / Part 1 Shot Pane */}
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: 0,
            width: `${leftWidthPct}%`,
            overflow: "hidden",
          }}
        >
          {src1 && (
            <Img
              src={src1}
              style={{
                width: "100%",
                height: "100%",
                objectFit: s1.framing_mode === "broadcast_card" ? "contain" : "cover",
                objectPosition: s1.framing_mode === "broadcast_card" ? "center 40%" : `${fx1}% ${fy1}%`,
                transformOrigin: s1.framing_mode === "broadcast_card" ? "center 40%" : `${fx1}% ${fy1}%`,
                transform: `scale(${zoom1})`,
                filter: "contrast(1.08) brightness(0.98) saturate(1.14)",
              }}
            />
          )}
        </div>

        {/* Right / Part 2 Shot Pane (Slides in cleanly at dilemma midpoint) */}
        {splitProgress > 0.005 && (
          <div
            style={{
              position: "absolute",
              top: 0,
              bottom: 0,
              left: "50%",
              width: "50%",
              overflow: "hidden",
              transform: `translateX(${rightTranslateXPct}%)`,
              willChange: "transform",
            }}
          >
            {src2 && (
              <Img
                src={src2}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: s2.framing_mode === "broadcast_card" ? "contain" : "cover",
                  objectPosition: s2.framing_mode === "broadcast_card" ? "center 40%" : `${fx2}% ${fy2}%`,
                  transformOrigin: s2.framing_mode === "broadcast_card" ? "center 40%" : `${fx2}% ${fy2}%`,
                  transform: `scale(${zoom2})`,
                  filter: "contrast(1.08) brightness(0.98) saturate(1.14)",
                }}
              />
            )}
          </div>
        )}

        {/* Glowing Studio Duel Divider Bar (Safely spans upper HUD -> lower subtitle band) */}
        {dividerOpacity > 0 && (
          <div
            style={{
              position: "absolute",
              left: "calc(50% - 2px)",
              top: 0,
              bottom: 0,
              width: 4,
              opacity: dividerOpacity,
              background:
                "linear-gradient(180deg, rgba(255,215,0,0.2) 0%, rgba(255,215,0,0.95) 25%, rgba(255,255,255,0.95) 50%, rgba(255,215,0,0.95) 75%, rgba(255,215,0,0.2) 100%)",
              boxShadow: "0 0 18px rgba(255, 215, 0, 0.7)",
              zIndex: 4,
              pointerEvents: "none",
            }}
          />
        )}

        {/* 1990s CRT Scanline & Atmospheric Vignette Layer */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "repeating-linear-gradient(0deg, rgba(0, 0, 0, 0.34) 0px, rgba(0, 0, 0, 0.34) 2px, transparent 2px, transparent 4px)",
            mixBlendMode: "multiply",
            pointerEvents: "none",
            opacity: 0.78,
            zIndex: 3,
          }}
        />
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
  }

  // Standard 1-shot or sequential multi-shot resolution with focal-point placement
  let activeShot: SceneShot | undefined = undefined;
  let activeImagePath = imagePath;
  let activeFrame = frame;
  let activeDuration = durationInFrames;
  let shotIndex = 0;

  if (shots && shots.length > 0) {
    let acc = 0;
    for (let i = 0; i < shots.length; i++) {
      const s = shots[i];
      if (frame >= acc && frame < acc + s.durationInFrames) {
        activeShot = s;
        activeImagePath = s.image_path;
        activeFrame = frame - acc;
        activeDuration = s.durationInFrames;
        shotIndex = i;
        break;
      }
      acc += s.durationInFrames;
    }
    if (!activeShot) {
      const lastIdx = shots.length - 1;
      const fallbackShot = shots[lastIdx];
      if (fallbackShot) {
        activeShot = fallbackShot;
        activeImagePath = fallbackShot.image_path;
        activeFrame = Math.max(0, frame - (acc - fallbackShot.durationInFrames));
        activeDuration = fallbackShot.durationInFrames;
        shotIndex = lastIdx;
      }
    }
  }

  const focalX = activeShot?.focal_x ?? 50;
  const focalY = activeShot?.focal_y ?? 25;
  const framingMode = activeShot?.framing_mode ?? "full_bleed";
  const panDir = activeShot?.pan_direction ?? motion?.direction ?? "center";

  // Smooth non-linear subject-anchored motion
  let scale = 1.0;
  let translateX = 0;
  let translateY = 0;

  if (framingMode === "broadcast_card") {
    // Keep studio monitor frame steady with gentle micro push-in
    scale = interpolate(activeFrame, [0, activeDuration], [1.0, 1.03], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  } else if (motionType === "subtle_push_in") {
    scale = interpolate(activeFrame, [0, activeDuration], [1.0, 1.08], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.25, 0.1, 0.25, 1),
    });
  } else if (motionType === "slow_pan") {
    scale = 1.07;
    const startX = panDir === "left" ? 18 : -18;
    const endX = panDir === "left" ? -18 : 18;
    translateX = interpolate(activeFrame, [0, activeDuration], [startX, endX], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.22, 1, 0.36, 1),
    });
  } else if (motionType === "pop_in") {
    const pop = spring({
      frame: activeFrame,
      fps,
      config: { damping: 15, mass: 0.65, stiffness: 125 },
    });
    scale = 0.96 + pop * 0.08;
  } else {
    scale = interpolate(activeFrame, [0, activeDuration], [1.02, 1.06], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  const resolvedSrc = resolveImgSrc(activeImagePath);

  // Purposeful Scene & Multi-Shot Entry Transition Engine (GPU transform/opacity/clipPath only)
  const effectiveTransType =
    shotIndex > 0 ? "shutter_wipe" : (transitionIn?.type || "cross_dissolve");
  const transDur = 8;
  const isTransitioning = activeFrame < transDur;
  const tProg = interpolate(activeFrame, [0, transDur], [0.0, 1.0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.22, 1, 0.36, 1),
  });

  let containerOpacity = 1.0;
  let transOffsetX = 0;
  let transOffsetY = 0;
  let transScale = 1.0;
  let clipPathVal: string | undefined = undefined;
  let flashOverlayOpacity = 0.0;
  let wipeAccentLeftPct: number | null = null;

  if (isTransitioning) {
    if (effectiveTransType === "camera_flash") {
      flashOverlayOpacity = interpolate(activeFrame, [0, 2, 7], [0.0, 0.28, 0.0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
      transScale = interpolate(tProg, [0, 1], [1.06, 1.0]);
      containerOpacity = interpolate(activeFrame, [0, 3], [0.72, 1.0], { extrapolateRight: "clamp" });
    } else if (effectiveTransType === "whip_pan") {
      transOffsetX = (1 - tProg) * 115;
      containerOpacity = interpolate(tProg, [0, 0.4, 1], [0.35, 0.85, 1.0]);
    } else if (effectiveTransType === "document_snap") {
      transOffsetY = (1 - tProg) * 44;
      transScale = interpolate(tProg, [0, 1], [0.97, 1.0]);
      containerOpacity = interpolate(tProg, [0, 0.5, 1], [0.45, 0.9, 1.0]);
    } else if (effectiveTransType === "shutter_wipe") {
      const pct = tProg * 112;
      clipPathVal = `polygon(0 0, ${pct}% 0, ${Math.max(0, pct - 12)}% 100%, 0 100%)`;
      wipeAccentLeftPct = Math.max(0, pct - 6);
    } else {
      // cross_dissolve / cross_fade_in
      containerOpacity = interpolate(tProg, [0, 1], [0.0, 1.0]);
      transScale = interpolate(tProg, [0, 1], [1.025, 1.0]);
    }
  }

  // Subtle 1990s CRT sync jitter & cathode shimmer
  const syncJitterX = framingMode === "broadcast_card" ? 0 : Math.sin(frame * 2.1) * 0.55;
  const currentTranslateX = translateX + syncJitterX + transOffsetX;
  const currentTranslateY = translateY + transOffsetY;
  const finalScale = scale * transScale;
  const phosphorFlicker = Math.sin(frame * 0.45) * 0.015 + 0.985;

  const imgPositionStyle: React.CSSProperties = {
    objectFit: "cover",
    objectPosition: `${focalX}% ${focalY}%`,
    transformOrigin: `${focalX}% ${focalY}%`,
  };

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        backgroundColor: "#0B132B",
        opacity: containerOpacity,
      }}
    >
      {/* 1. Primary Background Image Layer with Focal-Anchored Placement & CRT Grade */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: clipPathVal,
        }}
      >
        {resolvedSrc ? (
          <>
            <Img
              src={resolvedSrc}
              style={{
                width: "100%",
                height: "100%",
                ...imgPositionStyle,
                transform: `scale(${finalScale}) translate(${currentTranslateX}px, ${currentTranslateY}px)`,
                filter: "contrast(1.07) brightness(0.98) saturate(1.14) blur(0.35px)",
                willChange: "transform, opacity",
              }}
            />

            {/* Phosphor Glow / Bloom on Highlights */}
            <Img
              src={resolvedSrc}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                ...imgPositionStyle,
                transform: `scale(${finalScale}) translate(${currentTranslateX}px, ${currentTranslateY}px)`,
                filter: "blur(14px) brightness(1.25) saturate(1.18)",
                opacity: 0.24,
                mixBlendMode: "screen",
                pointerEvents: "none",
              }}
            />

            {/* Restrained Trinitron Aperture RGB Separation */}
            <Img
              src={resolvedSrc}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                ...imgPositionStyle,
                transform: `scale(${finalScale}) translate(${currentTranslateX - 1.8}px, ${currentTranslateY}px)`,
                filter: "hue-rotate(-25deg) saturate(1.35) blur(0.35px)",
                opacity: 0.14,
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
                ...imgPositionStyle,
                transform: `scale(${finalScale}) translate(${currentTranslateX + 1.8}px, ${currentTranslateY}px)`,
                filter: "hue-rotate(170deg) saturate(1.35) blur(0.35px)",
                opacity: 0.14,
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

      {/* 2. Exposure Glint Accent (camera_flash transition) */}
      {flashOverlayOpacity > 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "#FFFFFF",
            opacity: flashOverlayOpacity,
            pointerEvents: "none",
            zIndex: 5,
          }}
        />
      )}

      {/* 3. Angled Broadcast Wipe Gold/Cyan Lead Line (shutter_wipe transition) */}
      {wipeAccentLeftPct !== null && (
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            left: `${wipeAccentLeftPct}%`,
            width: 5,
            transform: "skewX(-6deg)",
            background:
              "linear-gradient(180deg, rgba(255, 215, 0, 0.92) 0%, rgba(56, 189, 248, 0.92) 50%, rgba(255, 255, 255, 0.92) 100%)",
            boxShadow: "0 0 14px rgba(56, 189, 248, 0.75)",
            zIndex: 4,
            pointerEvents: "none",
          }}
        />
      )}

      {/* 4. 1990s CRT Horizontal Scanlines & Vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "repeating-linear-gradient(0deg, rgba(0, 0, 0, 0.34) 0px, rgba(0, 0, 0, 0.34) 2px, transparent 2px, transparent 4px)",
          mixBlendMode: "multiply",
          pointerEvents: "none",
          opacity: 0.78 * phosphorFlicker,
          zIndex: 3,
        }}
      />
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
