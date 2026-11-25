import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  DocumentaryBeatProps,
  DocumentaryPaperProps,
  DocumentarySubtitleCue,
} from "./types";

function resolveDocSrc(rawPath?: string): string {
  if (!rawPath) return "";
  const norm = rawPath.replace(/\\/g, "/");
  if (norm.startsWith("data:") || norm.startsWith("http")) return norm;
  const rel = norm.replace(/^\//, "");
  try {
    return staticFile(rel);
  } catch {
    return "/" + rel;
  }
}

const EASE_OUT_EXPO = Easing.bezier(0.22, 1, 0.36, 1);

/** Aligned [FS30 Badge] + TV Bug + Era Archive Pill */
const DocumentaryTopHUD: React.FC<{ badgeSrc?: string; era: string }> = ({ badgeSrc, era }) => {
  const bSrc = resolveDocSrc(badgeSrc);
  return (
    <div
      style={{
        position: "absolute",
        top: 46,
        left: 38,
        right: 38,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        zIndex: 60,
        pointerEvents: "none",
      }}
    >
      {/* Unified Flexbox Brand Lockup */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {bSrc && (
          <Img
            src={bSrc}
            style={{
              width: 78,
              height: 78,
              objectFit: "contain",
              filter: "drop-shadow(0 6px 14px rgba(0, 0, 0, 0.78))",
            }}
          />
        )}
        <span
          style={{
            fontFamily: "'Anton', 'Barlow Condensed', sans-serif",
            fontWeight: 400,
            fontSize: 52,
            lineHeight: 1,
            letterSpacing: "0.04em",
            color: "#D90429",
            textShadow: "0 3px 10px rgba(0, 0, 0, 0.88)",
          }}
        >
          TV
        </span>
      </div>

      {/* Typewriter Archival Stamp Tag */}
      <div
        style={{
          fontFamily: "'Special Elite', 'Space Mono', monospace",
          fontWeight: 400,
          fontSize: 23,
          letterSpacing: "0.08em",
          color: "#F7F3E9",
          backgroundColor: "rgba(14, 16, 22, 0.84)",
          padding: "8px 18px",
          borderLeft: "4px solid #D90429",
          boxShadow: "0 6px 18px rgba(0,0,0,0.45)",
        }}
      >
        {(era || "ARCHIVE").toUpperCase()}
      </div>
    </div>
  );
};

/** Punchy High-Contrast Editorial Captions (Flexible auto-height, clear word spotlight) */
const DocumentarySubtitles: React.FC<{ subtitles: DocumentarySubtitleCue[] }> = ({ subtitles }) => {
  const frame = useCurrentFrame();
  const activeCue = subtitles.find((c) => frame >= c.start_frame && frame <= c.end_frame);
  if (!activeCue || !activeCue.words.length) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: 44,
        right: 44,
        bottom: 92,
        display: "flex",
        justifyContent: "center",
        zIndex: 55,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(12, 14, 20, 0.90)",
          padding: "12px 26px",
          borderLeft: "5px solid #FFE042",
          boxShadow: "0 14px 32px rgba(0,0,0,0.72)",
          maxWidth: 960,
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontFamily: "'Syne', 'Barlow Condensed', sans-serif",
            fontWeight: 800,
            fontSize: 34,
            lineHeight: 1.32,
            letterSpacing: "0.02em",
            color: "#F8F4EC",
          }}
        >
          {activeCue.words.map((w, i) => {
            const isActive = frame >= w.start_frame && frame <= w.end_frame;
            return (
              <span
                key={`${activeCue.id}-${i}`}
                style={{
                  display: "inline-block",
                  color: isActive ? "#FFE042" : "#F8F4EC",
                  transform: isActive ? "translateY(-2px)" : "translateY(0px)",
                  textShadow: isActive ? "0 0 12px rgba(255,224,66,0.45)" : "none",
                  marginRight: i < activeCue.words.length - 1 ? 15 : 0,
                }}
              >
                {w.word}
              </span>
            );
          })}
        </span>
      </div>
    </div>
  );
};

/** Dedicated Cheeky British Documentary Outro */
const DocumentaryOutro: React.FC<{
  badgeSrc?: string;
  bannerSrc?: string;
  headline: string;
  subtitle: string;
  cta: string;
}> = ({ badgeSrc, headline, subtitle, cta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const slam = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.65, stiffness: 135 },
  });
  const badgeScale = interpolate(slam, [0, 1], [1.28, 1.0]);
  const textFade = interpolate(frame, [4, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });
  const textY = interpolate(frame, [4, 14], [22, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });

  const bSrc = resolveDocSrc(badgeSrc);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0E1016",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 42%, rgba(46, 54, 74, 0.58) 0%, rgba(14, 16, 22, 0.96) 62%, #0A0C10 100%)",
        }}
      />

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: `scale(${badgeScale})`,
          marginBottom: 34,
        }}
      >
        {bSrc ? (
          <Img
            src={bSrc}
            style={{
              width: 380,
              height: 380,
              objectFit: "contain",
              filter: "drop-shadow(0 18px 34px rgba(0,0,0,0.85))",
            }}
          />
        ) : (
          <div
            style={{
              fontFamily: "'Anton', sans-serif",
              fontSize: 138,
              color: "#F7F4EC",
            }}
          >
            FS 30
          </div>
        )}
      </div>

      <div
        style={{
          opacity: textFade,
          transform: `translate3d(0, ${textY}px, 0)`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          padding: "0 64px",
        }}
      >
        <div
          style={{
            fontFamily: "'Anton', 'Barlow Condensed', sans-serif",
            fontSize: 66,
            lineHeight: 1.05,
            letterSpacing: "0.03em",
            color: "#F7F4EC",
            marginBottom: 14,
          }}
        >
          {headline}
        </div>
        <div
          style={{
            fontFamily: "'Playfair Display', 'Source Serif 4', serif",
            fontWeight: 700,
            fontStyle: "italic",
            fontSize: 36,
            lineHeight: 1.25,
            color: "#E5B824",
            marginBottom: 22,
          }}
        >
          {subtitle}
        </div>
        <div
          style={{
            fontFamily: "'Space Mono', monospace",
            fontWeight: 700,
            fontSize: 26,
            letterSpacing: "0.14em",
            color: "#F2EDE3",
            borderTop: "3px solid #D90429",
            paddingTop: 14,
          }}
        >
          {cta}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Single Beat Renderer: 12fps Paper Craft + Full-Frame Parallax + Sharp Transitions */
const DocumentaryBeatScene: React.FC<{
  beat: DocumentaryBeatProps;
  shared: DocumentaryPaperProps["shared_assets"];
}> = ({ beat, shared }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Signature Vox 12fps stepped stop-motion rhythm on collage/paper elements while background parallax glides @ 30fps
  const stepF = Math.floor(frame / 2.5) * 2.5;
  const paperStepRot = Math.sin(stepF * 0.42) * 0.65;
  const dur = Math.max(24, durationInFrames);

  // 1. High-Velocity Snappy Entry Transitions (compositor transform / opacity / clipPath only, 7-8 frames!)
  const transDur = 8;
  const tProg = interpolate(frame, [0, transDur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });

  let sceneClipPath: string | undefined = undefined;
  let sceneOpacity = 1;
  let sceneTransX = 0;
  let sceneTransY = 0;
  let sceneRotX = 0;
  let sceneScale = 1;
  let flashOpacity = 0;

  if (frame < transDur) {
    if (beat.transition_in === "torn_paper_wipe" || beat.transition_in === "jagged_paper_tear") {
      const pct = tProg * 118;
      sceneClipPath = `polygon(0 0, ${pct}% 0, ${Math.max(0, pct - 11)}% 24%, ${Math.max(0, pct - 4)}% 51%, ${Math.max(0, pct - 13)}% 76%, ${Math.max(0, pct - 6)}% 100%, 0 100%)`;
    } else if (beat.transition_in === "document_slide" || beat.transition_in === "card_flip_3d") {
      sceneTransY = (1 - tProg) * 76;
      sceneRotX = (1 - tProg) * 14;
      sceneOpacity = interpolate(tProg, [0, 0.4, 1], [0.2, 0.9, 1]);
    } else if (beat.transition_in === "shutter_flash" || beat.transition_in === "cutout_zoom_punch") {
      flashOpacity = interpolate(frame, [0, 2, 7], [0, 0.22, 0], { extrapolateRight: "clamp" });
      sceneScale = interpolate(tProg, [0, 1], [1.08, 1.0]);
      sceneOpacity = interpolate(frame, [0, 3], [0.68, 1], { extrapolateRight: "clamp" });
    } else {
      // Quick lateral match-cut swipe instead of sluggish fade
      sceneTransX = (1 - tProg) * 120;
      sceneOpacity = interpolate(tProg, [0, 0.5, 1], [0.3, 0.92, 1]);
    }
  }

  // 2. Plane 0 Opposing Camera Parallax
  let bgScale = interpolate(frame, [0, dur], [1.0, 1.06], { extrapolateRight: "clamp" });
  let bgPanX = 0;
  if (beat.camera_move === "pull_out") {
    bgScale = interpolate(frame, [0, dur], [1.08, 1.0], { extrapolateRight: "clamp" });
  } else if (beat.camera_move === "drift_left") {
    bgScale = 1.07;
    bgPanX = interpolate(frame, [0, dur], [20, -20], { extrapolateRight: "clamp" });
  } else if (beat.camera_move === "drift_right") {
    bgScale = 1.07;
    bgPanX = interpolate(frame, [0, dur], [-20, 20], { extrapolateRight: "clamp" });
  }

  // 3. Snappy Tight Entrance Curves (hero punches in immediately from frames 0..14!)
  const bannerIn = interpolate(frame, [2, 11], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });
  const heroIn = interpolate(frame, [3, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });
  const accentIn = interpolate(frame, [12, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });

  // 2.5D Opposing Cutout Drift + 12fps Stepped Organic Float
  const cutDriftScale = interpolate(frame, [3, dur], [1.0, 1.08], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cutFloatY = Math.sin(stepF * 0.14) * 5.5;
  const cutDriftX = -bgPanX * 0.9;

  const bgSrc = resolveDocSrc(beat.bg_path);
  const bannerSrc = resolveDocSrc(beat.banner_path);
  const textureSrc = resolveDocSrc(shared.paper_texture);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#101218",
        opacity: sceneOpacity,
        clipPath: sceneClipPath,
        overflow: "clip",
        transform: `perspective(1200px) translate3d(${sceneTransX}px, ${sceneTransY}px, 0) rotateX(${sceneRotX}deg) scale(${sceneScale})`,
      }}
    >
      {/* Plane 0: Atmospheric Desaturated Backdrop */}
      {bgSrc && beat.layout_style !== "clean_editorial_epilogue" && beat.layout_style !== "full_bleed_callout" && (
        <Img
          src={bgSrc}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${bgScale}) translate3d(${bgPanX}px, 0, 0)`,
            filter: "saturate(0.50) brightness(0.46) contrast(1.08)",
          }}
        />
      )}

      {/* Subtle Paper Grain Multiply Texture */}
      {textureSrc && beat.layout_style !== "clean_editorial_epilogue" && (
        <Img
          src={textureSrc}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            opacity: 0.16,
            mixBlendMode: "overlay",
            pointerEvents: "none",
          }}
        />
      )}

      {/* Giant Kinetic Background Word (slides smoothly BEHIND cutouts for rich depth) */}
      {beat.kinetic_word && beat.layout_style !== "clean_editorial_epilogue" && (
        <div
          style={{
            position: "absolute",
            left: -40,
            right: -40,
            top: 390,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            opacity: interpolate(heroIn, [0, 1], [0, 0.17]),
            transform: `translate3d(${interpolate(frame, [0, dur], [36, -36])}px, 0, 0) rotate(-4deg)`,
            zIndex: 14,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              fontFamily: "'Anton', sans-serif",
              fontSize: 215,
              lineHeight: 0.9,
              letterSpacing: "0.02em",
              color: "#F7F3E9",
              textTransform: "uppercase",
              textAlign: "center",
              whiteSpace: "nowrap",
            }}
          >
            {beat.kinetic_word}
          </div>
        </div>
      )}

      {/* Top/Bottom Editorial Contrast Gradient Scrim */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(14,16,22,0.72) 0%, rgba(14,16,22,0) 20%, rgba(14,16,22,0) 70%, rgba(14,16,22,0.92) 91%, #0E1016 100%)",
          pointerEvents: "none",
          zIndex: 18,
        }}
      />

      {/* Plane 1/2 Staggered Torn Paper Banner */}
      {bannerSrc && beat.layout_style !== "clean_editorial_epilogue" && (
        <div
          style={{
            position: "absolute",
            top: 136,
            left: 34,
            right: 34,
            display: "flex",
            justifyContent: "center",
            opacity: bannerIn,
            transform: `translate3d(0, ${(1 - bannerIn) * -36}px, 0) rotate(${paperStepRot * 0.45}deg)`,
            zIndex: 44,
            pointerEvents: "none",
          }}
        >
          <Img
            src={bannerSrc}
            style={{
              width: 970,
              height: "auto",
              maxHeight: 205,
              objectFit: "contain",
              filter: "drop-shadow(0 12px 22px rgba(0, 0, 0, 0.72))",
            }}
          />
        </div>
      )}

      {/* ===== LAYOUT 1: NEAR FULL-SCREEN 2.5D MULTIPLANE SUBJECT CUTOUT ===== */}
      {beat.layout_style === "vox_25d_cutout" && (beat.cutout || beat.mounted) && (
        <div
          style={{
            position: "absolute",
            top: beat.cutout ? 210 : 280,
            left: beat.cutout ? -24 : 20,
            right: beat.cutout ? -24 : 20,
            bottom: beat.cutout ? 65 : 150,
            display: "flex",
            justifyContent: "center",
            alignItems: beat.cutout ? "flex-end" : "center",
            opacity: heroIn,
            transform: `translate3d(${cutDriftX}px, ${(1 - heroIn) * 75 + cutFloatY}px, 0) scale(${cutDriftScale}) rotate(${paperStepRot * 0.5}deg)`,
            zIndex: 26,
          }}
        >
          <Img
            src={resolveDocSrc((beat.cutout || beat.mounted)?.path)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "contain",
              objectPosition: beat.cutout ? "center bottom" : "center center",
              filter: "drop-shadow(0 24px 36px rgba(0, 0, 0, 0.78))",
            }}
          />
        </div>
      )}

      {/* ===== LAYOUT 2: NEWSPAPER CLIPPING + GIANT FOREGROUND CUTOUT ===== */}
      {beat.layout_style === "newspaper_highlighter" && beat.newspaper_path && (
        <>
          <div
            style={{
              position: "absolute",
              top: 325,
              left: 44,
              right: 44,
              display: "flex",
              justifyContent: "center",
              opacity: heroIn,
              transform: `translate3d(0, ${(1 - heroIn) * 44}px, 0) rotate(-1.6deg) scale(${interpolate(frame, [3, dur], [0.99, 1.03], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })})`,
              zIndex: 28,
            }}
          >
            <div style={{ position: "relative", width: 960, filter: "drop-shadow(0 22px 32px rgba(0,0,0,0.78))" }}>
              <Img
                src={resolveDocSrc(beat.newspaper_path)}
                style={{ width: "100%", height: "auto", display: "block" }}
              />
              {(beat.highlight_rects || []).map((rect, idx) => {
                const startF = 14 + idx * 9;
                const wipe = interpolate(frame, [startF, startF + 14], [0, 100], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: EASE_OUT_EXPO,
                });
                return (
                  <div
                    key={idx}
                    style={{
                      position: "absolute",
                      left: `${rect.x_pct}%`,
                      top: `${rect.y_pct}%`,
                      width: `${rect.w_pct}%`,
                      height: `${rect.h_pct}%`,
                      backgroundColor: "rgba(255, 232, 30, 0.58)",
                      mixBlendMode: "multiply",
                      clipPath: `inset(0 ${100 - wipe}% 0 0)`,
                      borderRadius: 3,
                      pointerEvents: "none",
                    }}
                  />
                );
              })}
            </div>
          </div>

          {beat.cutout && (
            <div
              style={{
                position: "absolute",
                right: -24,
                bottom: 96,
                width: 860,
                height: 1120,
                opacity: heroIn,
                transform: `translate3d(${(1 - heroIn) * 90 + cutDriftX * 0.6}px, ${cutFloatY}px, 0) rotate(${paperStepRot * 0.65}deg)`,
                zIndex: 32,
              }}
            >
              <Img
                src={resolveDocSrc(beat.cutout.path)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  objectPosition: "right bottom",
                  filter: "drop-shadow(0 20px 30px rgba(0,0,0,0.82))",
                }}
              />
            </div>
          )}
        </>
      )}

      {/* ===== LAYOUT 3: FULL-BLEED DOCUMENTARY ACTION CALLOUT ===== */}
      {beat.layout_style === "full_bleed_callout" && (beat.editorial || beat.mounted) && (
        <AbsoluteFill style={{ zIndex: 22 }}>
          <Img
            src={resolveDocSrc((beat.editorial || beat.mounted)?.path)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: `${(beat.editorial || beat.mounted)?.focal_x ?? 50}% ${(beat.editorial || beat.mounted)?.focal_y ?? 30}%`,
              transformOrigin: `${(beat.editorial || beat.mounted)?.focal_x ?? 50}% ${(beat.editorial || beat.mounted)?.focal_y ?? 30}%`,
              transform: `scale(${interpolate(frame, [0, dur], [1.0, 1.09], { extrapolateRight: "clamp" })})`,
              filter: "contrast(1.08) brightness(0.92) saturate(1.08)",
            }}
          />
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "linear-gradient(180deg, rgba(14,16,22,0.72) 0%, rgba(14,16,22,0) 24%, rgba(14,16,22,0) 68%, rgba(14,16,22,0.92) 89%, #0E1016 100%)",
            }}
          />
          {beat.sub_caption && (
            <div
              style={{
                position: "absolute",
                left: 48,
                right: 48,
                bottom: 225,
                opacity: accentIn,
                transform: `translate3d(0, ${(1 - accentIn) * 26}px, 0)`,
                backgroundColor: "rgba(14, 16, 22, 0.85)",
                borderLeft: "6px solid #D90429",
                padding: "12px 22px",
              }}
            >
              <div
                style={{
                  fontFamily: "'Playfair Display', serif",
                  fontStyle: "italic",
                  fontWeight: 700,
                  fontSize: 34,
                  color: "#F7F3E9",
                }}
              >
                {beat.sub_caption}
              </div>
            </div>
          )}
        </AbsoluteFill>
      )}

      {/* ===== LAYOUT 4: NEAR FULL-WIDTH ARCHIVAL PINBOARD + ANIMATED SVG INK CIRCLE ===== */}
      {beat.layout_style === "archival_pinboard" && beat.mounted && (
        <div
          style={{
            position: "absolute",
            top: 335,
            left: 16,
            right: 16,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: heroIn,
            transform: `translate3d(0, ${(1 - heroIn) * 44}px, 0) rotate(-1.1deg) scale(${interpolate(frame, [3, dur], [0.99, 1.04], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })})`,
            zIndex: 25,
          }}
        >
          <div style={{ position: "relative", width: 1030 }}>
            <Img
              src={resolveDocSrc(beat.mounted.path)}
              style={{
                width: 1030,
                height: "auto",
                maxHeight: 1180,
                objectFit: "contain",
                display: "block",
              }}
            />

            {/* Animated Hand-Drawn SVG Marker Circle Drawing Live Around Target */}
            {beat.tactical_reticle?.enabled && (() => {
              const drawProg = interpolate(frame, [14, 34], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: EASE_OUT_EXPO,
              });
              const dashOffset = 660 * (1 - drawProg);
              return (
                <div
                  style={{
                    position: "absolute",
                    left: `${beat.tactical_reticle.target_x_pct ?? 50}%`,
                    top: `${beat.tactical_reticle.target_y_pct ?? 45}%`,
                    transform: "translate(-50%, -50%)",
                    opacity: drawProg > 0.02 ? 1 : 0,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    pointerEvents: "none",
                  }}
                >
                  <svg width="240" height="240" viewBox="0 0 240 240" style={{ overflow: "visible" }}>
                    <ellipse
                      cx="120"
                      cy="120"
                      rx="102"
                      ry="94"
                      fill="none"
                      stroke="#D90429"
                      strokeWidth="9"
                      strokeLinecap="round"
                      strokeDasharray="660"
                      strokeDashoffset={dashOffset}
                      style={{ filter: "drop-shadow(0 6px 14px rgba(0,0,0,0.65))" }}
                    />
                  </svg>
                  {beat.tactical_reticle.label && (
                    <div
                      style={{
                        marginTop: -6,
                        opacity: accentIn,
                        backgroundColor: "#D90429",
                        color: "#FFFFFF",
                        fontFamily: "'Space Mono', monospace",
                        fontWeight: 700,
                        fontSize: 22,
                        padding: "5px 14px",
                        letterSpacing: "0.08em",
                        boxShadow: "0 6px 16px rgba(0,0,0,0.55)",
                      }}
                    >
                      {beat.tactical_reticle.label.toUpperCase()}
                    </div>
                  )}
                </div>
              );
            })()}
          </div>

          {beat.sub_caption && (
            <div
              style={{
                marginTop: 14,
                fontFamily: "'Playfair Display', 'Source Serif 4', serif",
                fontStyle: "italic",
                fontWeight: 700,
                fontSize: 32,
                color: "#EFE8D5",
                textAlign: "center",
              }}
            >
              {beat.sub_caption}
            </div>
          )}
        </div>
      )}

      {/* ===== LAYOUT 5: KINETIC QUOTE / DOSSIER CARD + GIANT CUTOUT ===== */}
      {beat.layout_style === "kinetic_quote_card" && (
        <>
          {beat.quote_card_path && (
            <div
              style={{
                position: "absolute",
                top: 330,
                left: 36,
                right: 36,
                display: "flex",
                justifyContent: "center",
                opacity: heroIn,
                transform: `translate3d(${(1 - heroIn) * -70}px, 0, 0) rotate(${paperStepRot * 0.55 - 1.2}deg)`,
                zIndex: 27,
              }}
            >
              <Img
                src={resolveDocSrc(beat.quote_card_path)}
                style={{
                  width: 960,
                  height: "auto",
                  objectFit: "contain",
                  filter: "drop-shadow(0 20px 30px rgba(0,0,0,0.78))",
                }}
              />
            </div>
          )}

          {beat.cutout && (
            <div
              style={{
                position: "absolute",
                left: -20,
                bottom: 50,
                width: 740,
                height: 1120,
                opacity: heroIn,
                transform: `translate3d(${cutDriftX}px, ${(1 - heroIn) * 60 + cutFloatY}px, 0) scale(${cutDriftScale})`,
                zIndex: 31,
              }}
            >
              <Img
                src={resolveDocSrc(beat.cutout.path)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  objectPosition: "left bottom",
                  filter: "drop-shadow(0 20px 32px rgba(0,0,0,0.82))",
                }}
              />
            </div>
          )}
        </>
      )}

      {/* ===== LAYOUT 6: GIANT 2.5D ARTICULATED PUPPET CONFRONTATION ===== */}
      {beat.layout_style === "puppet_confrontation_25d" && (
        <div
          style={{
            position: "absolute",
            top: 290,
            left: 0,
            right: 0,
            bottom: 65,
            zIndex: 26,
          }}
        >
          {(() => {
            const p1In = interpolate(frame, [2, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT_EXPO });
            const p2In = interpolate(frame, [6, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT_EXPO });
            const strikeStart = Math.floor(dur * 0.34);
            const lunge = interpolate(frame, [strikeStart, strikeStart + 8, strikeStart + 18], [0, 1, 0.35], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: EASE_OUT_EXPO,
            });
            const recoil = interpolate(frame, [strikeStart + 4, strikeStart + 14], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: EASE_OUT_EXPO,
            });

            return (
              <>
                {beat.cutout && (
                  <div
                    style={{
                      position: "absolute",
                      left: -34,
                      bottom: 0,
                      width: 680,
                      height: 1280,
                      opacity: p1In,
                      transformOrigin: "45% 88%",
                      transform: `translate3d(${(1 - p1In) * -180 + lunge * 68}px, ${cutFloatY}px, 0) rotate(${lunge * 8.0}deg)`,
                    }}
                  >
                    <Img
                      src={resolveDocSrc(beat.cutout.path)}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        objectPosition: "left bottom",
                        filter: "drop-shadow(0 22px 32px rgba(0,0,0,0.82))",
                      }}
                    />
                  </div>
                )}

                {beat.secondary_cutout && (
                  <div
                    style={{
                      position: "absolute",
                      right: -34,
                      bottom: 0,
                      width: 680,
                      height: 1280,
                      opacity: p2In,
                      transformOrigin: "55% 88%",
                      transform: `translate3d(${(1 - p2In) * 180 + recoil * 44}px, ${-cutFloatY}px, 0) rotate(${recoil * 10.0}deg)`,
                    }}
                  >
                    <Img
                      src={resolveDocSrc(beat.secondary_cutout.path)}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        objectPosition: "right bottom",
                        filter: "drop-shadow(0 22px 32px rgba(0,0,0,0.82))",
                      }}
                    />
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {/* ===== LAYOUT 7: SNAPPY TACTILE CHRONOLOGICAL TIMELINE + GIANT CUTOUT ===== */}
      {beat.layout_style === "tactile_timeline_card" && (
        <div
          style={{
            position: "absolute",
            top: 345,
            left: 36,
            right: 24,
            bottom: 90,
            zIndex: 28,
          }}
        >
          {/* Fast Staggered Evidence Strips */}
          <div style={{ width: beat.cutout ? "58%" : "96%", display: "flex", flexDirection: "column", gap: 22 }}>
            {(beat.timeline_items || []).map((item, idx) => {
              const itemDelay = 5 + idx * 8;
              const p = interpolate(frame, [itemDelay, itemDelay + 9], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: EASE_OUT_EXPO,
              });
              return (
                <div
                  key={idx}
                  style={{
                    opacity: p,
                    transform: `translate3d(${(1 - p) * -65}px, 0, 0) rotate(${paperStepRot * 0.4}deg)`,
                    backgroundColor: "#F4EFE4",
                    borderLeft: "8px solid #D90429",
                    padding: "16px 22px",
                    boxShadow: "0 14px 28px rgba(0,0,0,0.62)",
                  }}
                >
                  <div
                    style={{
                      fontFamily: "'Space Mono', monospace",
                      fontWeight: 700,
                      fontSize: 22,
                      color: "#D90429",
                      letterSpacing: "0.06em",
                      marginBottom: 4,
                    }}
                  >
                    {item.year} // {item.event}
                  </div>
                  <div
                    style={{
                      fontFamily: "'Anton', 'Barlow Condensed', sans-serif",
                      fontSize: 34,
                      lineHeight: 1.08,
                      color: "#12151A",
                    }}
                  >
                    {item.detail}
                  </div>
                </div>
              );
            })}
          </div>

          {beat.cutout && (
            <div
              style={{
                position: "absolute",
                right: -30,
                bottom: -35,
                width: 640,
                height: 1240,
                opacity: heroIn,
                transform: `translate3d(${(1 - heroIn) * 70 + cutDriftX * 0.4}px, ${cutFloatY}px, 0) rotate(${paperStepRot * 0.4}deg)`,
                zIndex: 30,
              }}
            >
              <Img
                src={resolveDocSrc(beat.cutout.path)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  objectPosition: "right bottom",
                  filter: "drop-shadow(0 20px 32px rgba(0,0,0,0.82))",
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* ===== LAYOUT 8: FULL-BLEED EDITORIAL MAGAZINE COVER OR CAMP NOU SPREAD EPILOGUE ===== */}
      {beat.layout_style === "clean_editorial_epilogue" && (
        <AbsoluteFill style={{ zIndex: 22 }}>
          {beat.bg_path && !beat.editorial && (
            <Img
              src={resolveDocSrc(beat.bg_path)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                transform: `scale(${bgScale * 1.05})`,
                filter: "grayscale(0.32) contrast(1.12) brightness(0.45)",
              }}
            />
          )}
          {beat.editorial && (
            <Img
              src={resolveDocSrc(beat.editorial.path)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: `${beat.editorial.focal_x ?? 50}% ${beat.editorial.focal_y ?? 25}%`,
                transformOrigin: `${beat.editorial.focal_x ?? 50}% ${beat.editorial.focal_y ?? 25}%`,
                transform: `scale(${bgScale})`,
                filter: "contrast(1.08) brightness(0.90) saturate(0.98)",
              }}
            />
          )}
          {beat.mounted && !beat.editorial && (
            <div
              style={{
                position: "absolute",
                top: 230,
                left: 14,
                right: 14,
                display: "flex",
                justifyContent: "center",
                opacity: heroIn,
                transform: `translate3d(0, ${(1 - heroIn) * 34}px, 0) scale(${bgScale})`,
              }}
            >
              <Img
                src={resolveDocSrc(beat.mounted.path)}
                style={{
                  width: 1036,
                  height: "auto",
                  maxHeight: 1120,
                  objectFit: "contain",
                  filter: "drop-shadow(0 26px 38px rgba(0,0,0,0.85))",
                }}
              />
            </div>
          )}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "linear-gradient(180deg, rgba(14,16,22,0.52) 0%, rgba(14,16,22,0) 24%, rgba(14,16,22,0.18) 54%, rgba(14,16,22,0.92) 84%, #0E1016 100%)",
            }}
          />
          <div
            style={{
              position: "absolute",
              left: 52,
              right: 52,
              bottom: 225,
              opacity: heroIn,
              transform: `translate3d(0, ${(1 - heroIn) * 32}px, 0)`,
            }}
          >
            <div
              style={{
                fontFamily: "'Space Mono', monospace",
                fontWeight: 700,
                fontSize: 22,
                letterSpacing: "0.14em",
                color: "#FFE042",
                marginBottom: 8,
              }}
            >
              {beat.visual_kicker}
            </div>
            <div
              style={{
                fontFamily: "'Anton', 'Barlow Condensed', sans-serif",
                fontSize: 84,
                lineHeight: 0.96,
                letterSpacing: "0.02em",
                color: "#F7F4EC",
                textShadow: "0 6px 20px rgba(0,0,0,0.65)",
                marginBottom: 12,
              }}
            >
              {beat.visual_headline}
            </div>
            {beat.sub_caption && (
              <div
                style={{
                  fontFamily: "'Playfair Display', 'Source Serif 4', serif",
                  fontStyle: "italic",
                  fontWeight: 700,
                  fontSize: 34,
                  color: "#E7DFCA",
                }}
              >
                {beat.sub_caption}
              </div>
            )}
          </div>
        </AbsoluteFill>
      )}

      {/* Optional Distressed Red Rubber Stamp */}
      {beat.stamp_path && (
        (() => {
          const stStart = Math.max(18, Math.floor(dur * 0.44));
          const sp = spring({
            frame: Math.max(0, frame - stStart),
            fps,
            config: { damping: 12, mass: 0.55, stiffness: 170 },
          });
          const vis = frame >= stStart ? 1 : 0;
          const stScale = interpolate(sp, [0, 1], [1.48, 1.0]);
          const posTop =
            beat.layout_style === "newspaper_highlighter"
              ? 880
              : beat.layout_style === "puppet_confrontation_25d"
                ? 365
                : beat.layout_style === "kinetic_quote_card"
                  ? 760
                  : 1245;
          const posLeft =
            beat.layout_style === "newspaper_highlighter"
              ? 48
              : beat.layout_style === "puppet_confrontation_25d"
                ? 320
                : 550;
          return (
            <div
              style={{
                position: "absolute",
                top: posTop,
                left: posLeft,
                opacity: vis,
                transform: `scale(${stScale}) rotate(${paperStepRot * 0.6}deg)`,
                zIndex: 42,
                pointerEvents: "none",
              }}
            >
              <Img
                src={resolveDocSrc(beat.stamp_path)}
                style={{
                  width: 420,
                  height: "auto",
                  objectFit: "contain",
                  filter: "drop-shadow(0 8px 16px rgba(0,0,0,0.58))",
                }}
              />
            </div>
          );
        })()
      )}

      {/* Optional Subtle Transition Impact Flash */}
      {flashOpacity > 0.005 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: "#FFF9E6",
            opacity: flashOpacity,
            pointerEvents: "none",
            zIndex: 50,
          }}
        />
      )}
    </AbsoluteFill>
  );
};

export const DocumentaryPaperShort: React.FC<DocumentaryPaperProps> = ({
  era,
  totalDurationInFrames,
  outroDurationInFrames,
  outro_headline,
  outro_subtitle,
  outro_cta,
  shared_assets,
  beats,
  subtitles,
}) => {
  const globalFrame = useCurrentFrame();
  const storyEndFrame = Math.max(
    0,
    (totalDurationInFrames || 1500) - (outroDurationInFrames || 114)
  );
  let accFrame = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#0E1016" }}>
      {beats.map((beat) => {
        const startFrame = accFrame;
        accFrame += beat.durationInFrames;

        if (beat.layout_style === "fs30_brand_outro") {
          return (
            <Sequence
              key={`beat-${beat.beat_number}`}
              from={startFrame}
              durationInFrames={beat.durationInFrames || outroDurationInFrames || 110}
            >
              <DocumentaryOutro
                badgeSrc={shared_assets?.badge}
                headline={outro_headline}
                subtitle={outro_subtitle}
                cta={outro_cta}
              />
            </Sequence>
          );
        }

        return (
          <Sequence
            key={`beat-${beat.beat_number}`}
            from={startFrame}
            durationInFrames={beat.durationInFrames}
          >
            <DocumentaryBeatScene beat={beat} shared={shared_assets} />
          </Sequence>
        );
      })}

      {/* Persistent Unified Logo + TV Bug (cleanly hides on dedicated Outro card) */}
      {globalFrame < storyEndFrame && (
        <DocumentaryTopHUD badgeSrc={shared_assets?.badge} era={era} />
      )}

      {/* Consistent Clean Documentary Subtitles */}
      <DocumentarySubtitles subtitles={subtitles || []} />
    </AbsoluteFill>
  );
};
