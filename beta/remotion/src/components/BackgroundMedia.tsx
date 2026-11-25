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

const FloatingClubCrest: React.FC<{
  crestPath?: string;
  clubLabel?: string;
  frame: number;
  fps: number;
  startDelay?: number;
  compact?: boolean;
}> = ({ crestPath, clubLabel, frame, fps, startDelay = 3, compact = false }) => {
  const src = resolveImgSrc(crestPath);
  if (!src) return null;

  const relFrame = Math.max(0, frame - startDelay);
  const pop = spring({
    frame: relFrame,
    fps,
    config: { damping: 14, mass: 0.68, stiffness: 145 },
  });
  const opacity = interpolate(relFrame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  const scale = interpolate(pop, [0, 1], [0.72, 1.0]);
  const logoSize = compact ? 240 : 340;

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: 220,
        bottom: 690,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity,
        transform: `scale(${scale})`,
        transformOrigin: "center center",
        zIndex: 5,
        pointerEvents: "none",
        willChange: "transform, opacity",
      }}
    >
      <div
        style={{
          position: "relative",
          width: logoSize,
          height: logoSize,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Soft studio radial spotlight so dark/monochrome crests (e.g. Juventus JJ) pop cleanly off stadiums */}
        <div
          style={{
            position: "absolute",
            inset: -44,
            borderRadius: "50%",
            background:
              "radial-gradient(circle, rgba(255,255,255,0.42) 0%, rgba(255,255,255,0.16) 46%, rgba(255,255,255,0) 74%)",
            pointerEvents: "none",
          }}
        />
        <Img
          src={src}
          style={{
            position: "relative",
            width: logoSize,
            height: logoSize,
            objectFit: "contain",
            filter:
              "drop-shadow(0 0 4px rgba(255, 255, 255, 0.72)) drop-shadow(0 16px 32px rgba(0, 0, 0, 0.92))",
          }}
        />
      </div>
      {clubLabel && (
        <div
          style={{
            marginTop: 18,
            padding: compact ? "7px 16px" : "9px 24px",
            backgroundColor: "rgba(11, 19, 43, 0.88)",
            border: "2px solid rgba(255, 215, 0, 0.88)",
            borderRadius: 6,
            boxShadow: "0 10px 24px rgba(0, 0, 0, 0.72)",
            color: "#FFFFFF",
            fontSize: compact ? 22 : 28,
            fontWeight: 900,
            letterSpacing: "0.09em",
            textTransform: "uppercase",
            fontFamily: "system-ui, -apple-system, sans-serif",
            textAlign: "center",
          }}
        >
          {clubLabel}
        </div>
      )}
    </div>
  );
};

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
  const isDualLandscapeSplit =
    motionType === "dual_landscape_split" && shots && shots.length >= 2;

  // Dynamic Stacked Dual-Landscape Split (Top half slides from LEFT, Bottom half slides from RIGHT)
  if (isDualLandscapeSplit && shots) {
    const topShot = shots[0];
    const botShot = shots[1];
    const topSrc = resolveImgSrc(topShot.image_path);
    const botSrc = resolveImgSrc(botShot.image_path);
    const tfx = topShot.focal_x ?? 50;
    const tfy = topShot.focal_y ?? 30;
    const bfx = botShot.focal_x ?? 50;
    const bfy = botShot.focal_y ?? 30;

    const slideEase = Easing.bezier(0.22, 1, 0.36, 1);
    const topSlideProg = interpolate(frame, [0, 11], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: slideEase,
    });
    const botSlideProg = interpolate(frame, [4, 15], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: slideEase,
    });

    const topSlideX = (1 - topSlideProg) * -1080;
    const botSlideX = (1 - botSlideProg) * 1080;
    const topDriftX = interpolate(frame, [0, durationInFrames], [-14, 14], {
      extrapolateRight: "clamp",
    });
    const botDriftX = interpolate(frame, [0, durationInFrames], [14, -14], {
      extrapolateRight: "clamp",
    });
    const bandScale = interpolate(frame, [0, durationInFrames], [1.03, 1.08], {
      extrapolateRight: "clamp",
    });
    const seamOpacity = interpolate(frame, [8, 16], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });

    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          overflow: "clip",
          backgroundColor: "#0B132B",
        }}
      >
        {/* Ambient blurred studio backdrop above TopHUD & below Subtitles */}
        {topSrc && (
          <Img
            src={topSrc}
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: "scale(1.16)",
              filter: "blur(26px) brightness(0.36) saturate(1.15)",
            }}
          />
        )}

        {/* Top Landscape Band (y: 192..728) sliding in cleanly from LEFT */}
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 192,
            width: 1080,
            height: 536,
            overflow: "clip",
            transform: `translate3d(${topSlideX}px, 0, 0)`,
            willChange: "transform",
            borderTop: "2px solid rgba(255, 215, 0, 0.45)",
          }}
        >
          {topSrc && (
            <Img
              src={topSrc}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: `${tfx}% ${tfy}%`,
                transformOrigin: `${tfx}% ${tfy}%`,
                transform: `scale(${bandScale}) translate3d(${topDriftX}px, 0, 0)`,
                filter: "contrast(1.08) brightness(0.98) saturate(1.15)",
              }}
            />
          )}
        </div>

        {/* Bottom Landscape Band (y: 736..1272) sliding in cleanly from RIGHT */}
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 736,
            width: 1080,
            height: 536,
            overflow: "clip",
            transform: `translate3d(${botSlideX}px, 0, 0)`,
            willChange: "transform",
            borderBottom: "2px solid rgba(56, 189, 248, 0.45)",
          }}
        >
          {botSrc && (
            <Img
              src={botSrc}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: `${bfx}% ${bfy}%`,
                transformOrigin: `${bfx}% ${bfy}%`,
                transform: `scale(${bandScale}) translate3d(${botDriftX}px, 0, 0)`,
                filter: "contrast(1.08) brightness(0.98) saturate(1.15)",
              }}
            />
          )}
        </div>

        {/* Center Horizontal Broadcast Seam Bar */}
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 728,
            height: 8,
            opacity: seamOpacity,
            background:
              "linear-gradient(90deg, rgba(255,215,0,0.35) 0%, #FFD700 35%, #FFFFFF 50%, #38BDF8 65%, rgba(56,189,248,0.35) 100%)",
            boxShadow: "0 0 18px rgba(255, 215, 0, 0.65)",
            zIndex: 4,
            pointerEvents: "none",
          }}
        />

        {/* 1990s CRT Scanlines & Upper/Lower Edge Scrims */}
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
              "linear-gradient(180deg, rgba(11, 19, 43, 0.85) 0%, rgba(11, 19, 43, 0) 14%, rgba(11, 19, 43, 0) 68%, rgba(11, 19, 43, 0.94) 85%, #0B132B 100%)",
            pointerEvents: "none",
            zIndex: 2,
          }}
        />
      </div>
    );
  }

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
          overflow: "clip",
          backgroundColor: "#0B132B",
          transform: `translate3d(${entryOffsetX}px, 0, 0)`,
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
            overflow: "clip",
          }}
        >
          {src1 && (
            <Img
              src={src1}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: `${fx1}% ${fy1}%`,
                transformOrigin: `${fx1}% ${fy1}%`,
                transform: `scale(${zoom1})`,
                filter: s1.overlay_crest_path
                  ? "contrast(1.08) brightness(0.74) saturate(1.12)"
                  : "contrast(1.08) brightness(0.98) saturate(1.14)",
              }}
            />
          )}
          <FloatingClubCrest
            crestPath={s1.overlay_crest_path}
            clubLabel={s1.club_label}
            frame={frame}
            fps={fps}
            startDelay={4}
            compact
          />
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
              overflow: "clip",
              transform: `translate3d(${rightTranslateXPct}%, 0, 0)`,
              willChange: "transform",
            }}
          >
            {src2 && (
              <Img
                src={src2}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: `${fx2}% ${fy2}%`,
                  transformOrigin: `${fx2}% ${fy2}%`,
                  transform: `scale(${zoom2})`,
                  filter: s2.overlay_crest_path
                    ? "contrast(1.08) brightness(0.72) saturate(1.12)"
                    : "contrast(1.08) brightness(0.98) saturate(1.14)",
                }}
              />
            )}
            <FloatingClubCrest
              crestPath={s2.overlay_crest_path}
              clubLabel={s2.club_label}
              frame={frame}
              fps={fps}
              startDelay={splitStart + 2}
              compact
            />
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
  } else if (framingMode === "pan_horizontal" || motionType === "slow_pan") {
    scale = framingMode === "pan_horizontal" ? 1.09 : 1.07;
    const sweep = framingMode === "pan_horizontal" ? 30 : 18;
    const startX = panDir === "left" ? sweep : -sweep;
    const endX = panDir === "left" ? -sweep : sweep;
    translateX = interpolate(activeFrame, [0, activeDuration], [startX, endX], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.22, 1, 0.36, 1),
    });
  } else if (motionType === "subtle_push_in") {
    scale = interpolate(activeFrame, [0, activeDuration], [1.0, 1.08], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.25, 0.1, 0.25, 1),
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

  const hasCrestOverlay = Boolean(activeShot?.overlay_crest_path);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "clip",
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
                transform: `scale(${finalScale}) translate3d(${currentTranslateX}px, ${currentTranslateY}px, 0)`,
                filter: hasCrestOverlay
                  ? "contrast(1.07) brightness(0.75) saturate(1.12) blur(0.45px)"
                  : "contrast(1.07) brightness(0.98) saturate(1.14) blur(0.35px)",
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
                transform: `scale(${finalScale}) translate3d(${currentTranslateX}px, ${currentTranslateY}px, 0)`,
                filter: "blur(14px) brightness(1.25) saturate(1.18)",
                opacity: hasCrestOverlay ? 0.14 : 0.24,
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
                transform: `scale(${finalScale}) translate3d(${currentTranslateX - 1.8}px, ${currentTranslateY}px, 0)`,
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
                transform: `scale(${finalScale}) translate3d(${currentTranslateX + 1.8}px, ${currentTranslateY}px, 0)`,
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

      {/* 1b. Transparent Background-Cut Club Emblem Floating Over Stadium / Backdrop */}
      {hasCrestOverlay && (
        <FloatingClubCrest
          crestPath={activeShot?.overlay_crest_path}
          clubLabel={activeShot?.club_label}
          frame={activeFrame}
          fps={fps}
          startDelay={4}
        />
      )}

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
