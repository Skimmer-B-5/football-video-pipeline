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
        top: 64,
        left: 48,
        right: 48,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        zIndex: 60,
        pointerEvents: "none",
      }}
    >
      {/* Unified Flexbox Brand Lockup — fixes vertical baseline offset permanently */}
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        {bSrc && (
          <Img
            src={bSrc}
            style={{
              width: 86,
              height: 86,
              objectFit: "contain",
              filter: "drop-shadow(0 6px 14px rgba(0, 0, 0, 0.72))",
            }}
          />
        )}
        <span
          style={{
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 900,
            fontSize: 56,
            lineHeight: 1,
            letterSpacing: "0.02em",
            color: "#D90429",
            textShadow: "0 3px 10px rgba(0, 0, 0, 0.85)",
          }}
        >
          TV
        </span>
      </div>

      {/* Restrained Mono Archive Tag */}
      <div
        style={{
          fontFamily: "'IBM Plex Mono', 'IBM Plex Sans', monospace",
          fontWeight: 600,
          fontSize: 21,
          letterSpacing: "0.1em",
          color: "#F2EDE3",
          backgroundColor: "rgba(16, 18, 24, 0.78)",
          padding: "8px 18px",
          borderLeft: "3px solid #D90429",
        }}
      >
        {(era || "ARCHIVE").toUpperCase()}
      </div>
    </div>
  );
};

/** Clean Restrained Documentary Subtitles (No chaotic neon blobs or giant bounce boxes) */
const DocumentarySubtitles: React.FC<{ subtitles: DocumentarySubtitleCue[] }> = ({ subtitles }) => {
  const frame = useCurrentFrame();
  const activeCue = subtitles.find((c) => frame >= c.start_frame && frame <= c.end_frame);
  if (!activeCue || !activeCue.words.length) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        right: 64,
        bottom: 132,
        display: "flex",
        justifyContent: "center",
        zIndex: 55,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(14, 16, 22, 0.84)",
          padding: "12px 24px",
          borderBottom: "2px solid rgba(255, 224, 66, 0.55)",
          maxWidth: 920,
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontFamily: "'IBM Plex Sans', 'Inter', sans-serif",
            fontWeight: 600,
            fontSize: 34,
            lineHeight: 1.32,
            letterSpacing: "0.01em",
            color: "#F7F4EC",
          }}
        >
          {activeCue.words.map((w, i) => {
            const isActive = frame >= w.start_frame && frame <= w.end_frame;
            return (
              <span
                key={`${activeCue.id}-${i}`}
                style={{
                  color: isActive ? "#FFE042" : "#F7F4EC",
                  fontWeight: isActive ? 700 : 600,
                  marginRight: i < activeCue.words.length - 1 ? 10 : 0,
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

/** Dedicated Restrained FS30 Documentary Outro */
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
    config: { damping: 14, mass: 0.7, stiffness: 115 },
  });
  const badgeScale = interpolate(slam, [0, 1], [1.26, 1.0]);
  const textFade = interpolate(frame, [8, 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });
  const textY = interpolate(frame, [8, 22], [24, 0], {
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
      {/* Subtle Radial Vignette Spotlight */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 42%, rgba(42, 50, 68, 0.55) 0%, rgba(14, 16, 22, 0.96) 62%, #0A0C10 100%)",
        }}
      />

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          transform: `scale(${badgeScale})`,
          marginBottom: 40,
        }}
      >
        {bSrc ? (
          <Img
            src={bSrc}
            style={{
              width: 380,
              height: 380,
              objectFit: "contain",
              filter: "drop-shadow(0 18px 34px rgba(0,0,0,0.8))",
            }}
          />
        ) : (
          <div
            style={{
              fontFamily: "'Barlow Condensed', sans-serif",
              fontWeight: 900,
              fontSize: 132,
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
          transform: `translateY(${textY}px)`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          padding: "0 72px",
        }}
      >
        <div
          style={{
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 800,
            fontSize: 60,
            letterSpacing: "0.02em",
            color: "#F7F4EC",
            marginBottom: 14,
          }}
        >
          {headline}
        </div>
        <div
          style={{
            fontFamily: "'Source Serif 4', serif",
            fontWeight: 700,
            fontStyle: "italic",
            fontSize: 34,
            color: "#E5B824",
            marginBottom: 22,
          }}
        >
          {subtitle}
        </div>
        <div
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontWeight: 600,
            fontSize: 26,
            letterSpacing: "0.14em",
            color: "#F2EDE3",
            borderTop: "2px solid #D90429",
            paddingTop: 14,
          }}
        >
          {cta}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/** Single Beat Renderer: Multiplane Parallax + Staggered Reveals + Transitions */
const DocumentaryBeatScene: React.FC<{
  beat: DocumentaryBeatProps;
  shared: DocumentaryPaperProps["shared_assets"];
}> = ({ beat, shared }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Tactile 15fps stepped subtlety for authentic paper-cut motion feel on cutouts/widgets while camera stays smooth
  const stepF = Math.floor(frame / 2) * 2;
  const dur = Math.max(30, durationInFrames);

  // 1. Entry Transition Progress (compositor transform / opacity / clipPath only)
  const transDur = 10;
  const tProg = interpolate(frame, [0, transDur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });

  let sceneClipPath: string | undefined = undefined;
  let sceneOpacity = 1;
  let sceneTransX = 0;
  let sceneTransY = 0;
  let flashOpacity = 0;

  if (frame < transDur) {
    if (beat.transition_in === "torn_paper_wipe") {
      const pct = tProg * 116;
      sceneClipPath = `polygon(0 0, ${pct}% 0, ${Math.max(0, pct - 9)}% 33%, ${Math.max(0, pct - 4)}% 68%, ${Math.max(0, pct - 11)}% 100%, 0 100%)`;
    } else if (beat.transition_in === "document_slide") {
      sceneTransY = (1 - tProg) * 56;
      sceneOpacity = interpolate(tProg, [0, 0.5, 1], [0.25, 0.85, 1]);
    } else if (beat.transition_in === "shutter_flash") {
      flashOpacity = interpolate(frame, [0, 2, 8], [0, 0.24, 0], { extrapolateRight: "clamp" });
      sceneOpacity = interpolate(frame, [0, 3], [0.65, 1], { extrapolateRight: "clamp" });
    } else {
      sceneOpacity = tProg;
    }
  }

  // 2. Plane 0 Opposing Camera Parallax
  let bgScale = interpolate(frame, [0, dur], [1.0, 1.045], { extrapolateRight: "clamp" });
  let bgPanX = 0;
  if (beat.camera_move === "pull_out") {
    bgScale = interpolate(frame, [0, dur], [1.055, 1.0], { extrapolateRight: "clamp" });
  } else if (beat.camera_move === "drift_left") {
    bgScale = 1.05;
    bgPanX = interpolate(frame, [0, dur], [14, -14], { extrapolateRight: "clamp" });
  } else if (beat.camera_move === "drift_right") {
    bgScale = 1.05;
    bgPanX = interpolate(frame, [0, dur], [-14, 14], { extrapolateRight: "clamp" });
  }

  // 3. Staggered Sequential Entrance Curves (No Frame-0 Asset Clutter!)
  const bannerIn = interpolate(frame, [6, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });
  const heroIn = interpolate(frame, [12, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });
  const accentIn = interpolate(frame, [28, 44], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT_EXPO,
  });

  // 2.5D Opposing Cutout Drift + Soft Organic Float (aspect-locked!)
  const cutDriftScale = interpolate(frame, [12, dur], [0.98, 1.06], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cutFloatY = Math.sin(stepF * 0.085) * 4.5;
  const cutDriftX = -bgPanX * 0.85; // Counter-direction creates real multiplane depth!

  const bgSrc = resolveDocSrc(beat.bg_path);
  const bannerSrc = resolveDocSrc(beat.banner_path);
  const textureSrc = resolveDocSrc(shared.paper_texture);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#101218",
        opacity: sceneOpacity,
        clipPath: sceneClipPath,
        transform: `translate3d(${sceneTransX}px, ${sceneTransY}px, 0)`,
      }}
    >
      {/* Plane 0: Atmospheric Desaturated Backdrop */}
      {bgSrc && beat.layout_style !== "clean_editorial_epilogue" && (
        <Img
          src={bgSrc}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${bgScale}) translateX(${bgPanX}px)`,
            filter: "saturate(0.45) brightness(0.42) contrast(1.06)",
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
            opacity: 0.14,
            mixBlendMode: "overlay",
            pointerEvents: "none",
          }}
        />
      )}

      {/* Top/Bottom Editorial Contrast Gradient Scrim */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(14,16,22,0.72) 0%, rgba(14,16,22,0) 24%, rgba(14,16,22,0) 64%, rgba(14,16,22,0.92) 90%, #0E1016 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Plane 1/2 Staggered Torn Paper Banner (Selected alternating scenes) */}
      {bannerSrc && beat.layout_style !== "clean_editorial_epilogue" && (
        <div
          style={{
            position: "absolute",
            top: 175,
            left: 48,
            right: 48,
            display: "flex",
            justifyContent: "center",
            opacity: bannerIn,
            transform: `translateY(${(1 - bannerIn) * -32}px)`,
            zIndex: 35,
            pointerEvents: "none",
          }}
        >
          <Img
            src={bannerSrc}
            style={{
              width: 920,
              height: "auto",
              maxHeight: 220,
              objectFit: "contain",
              filter: "drop-shadow(0 12px 22px rgba(0, 0, 0, 0.65))",
            }}
          />
        </div>
      )}

      {/* ===== LAYOUT 1: VOX 2.5D MULTIPLANE SUBJECT CUTOUT ===== */}
      {beat.layout_style === "vox_25d_cutout" && beat.cutout && (
        <div
          style={{
            position: "absolute",
            top: 390,
            left: 70,
            right: 70,
            bottom: 245,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            opacity: heroIn,
            transform: `translate3d(${cutDriftX}px, ${(1 - heroIn) * 60 + cutFloatY}px, 0) scale(${cutDriftScale})`,
            zIndex: 25,
          }}
        >
          <Img
            src={resolveDocSrc(beat.cutout.path)}
            style={{
              maxWidth: "100%",
              maxHeight: "100%",
              width: "auto",
              height: "100%",
              objectFit: "contain",
              filter: "drop-shadow(0 22px 30px rgba(0, 0, 0, 0.72))",
            }}
          />
        </div>
      )}

      {/* ===== LAYOUT 2: NEWSPAPER CLIPPING + ANIMATED HIGHLIGHTER WIPE ===== */}
      {beat.layout_style === "newspaper_highlighter" && beat.newspaper_path && (
        <>
          <div
            style={{
              position: "absolute",
              top: 410,
              left: 72,
              right: 72,
              display: "flex",
              justifyContent: "center",
              opacity: heroIn,
              transform: `translateY(${(1 - heroIn) * 48}px) rotate(-1.3deg) scale(${interpolate(frame, [12, dur], [0.99, 1.03], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })})`,
              zIndex: 26,
            }}
          >
            <div style={{ position: "relative", width: 920, filter: "drop-shadow(0 20px 30px rgba(0,0,0,0.72))" }}>
              <Img
                src={resolveDocSrc(beat.newspaper_path)}
                style={{ width: "100%", height: "auto", display: "block" }}
              />
              {/* Yellow Neon Highlighter Wipe Sweeping Phrase */}
              {(beat.highlight_rects || []).map((rect, idx) => {
                const startF = 30 + idx * 12;
                const wipe = interpolate(frame, [startF, startF + 18], [0, 100], {
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
                      backgroundColor: "rgba(255, 232, 30, 0.56)",
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
                right: 42,
                bottom: 225,
                width: 470,
                height: 620,
                opacity: accentIn,
                transform: `translate3d(${(1 - accentIn) * 70 + cutDriftX * 0.5}px, ${cutFloatY}px, 0)`,
                zIndex: 32,
              }}
            >
              <Img
                src={resolveDocSrc(beat.cutout.path)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  filter: "drop-shadow(0 18px 26px rgba(0,0,0,0.78))",
                }}
              />
            </div>
          )}
        </>
      )}

      {/* ===== LAYOUT 3: ARCHIVAL PINBOARD PHOTO + RED INK RETICLE ===== */}
      {beat.layout_style === "archival_pinboard" && beat.mounted && (
        <div
          style={{
            position: "absolute",
            top: 425,
            left: 56,
            right: 56,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: heroIn,
            transform: `translateY(${(1 - heroIn) * 44}px) scale(${interpolate(frame, [12, dur], [0.99, 1.04], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })})`,
            zIndex: 25,
          }}
        >
          <div style={{ position: "relative", maxWidth: 940 }}>
            <Img
              src={resolveDocSrc(beat.mounted.path)}
              style={{
                width: 920,
                height: "auto",
                maxHeight: 820,
                objectFit: "contain",
                display: "block",
              }}
            />

            {/* Hand-Drawn Red Ink Circle & Label */}
            {beat.tactical_reticle?.enabled && (
              <div
                style={{
                  position: "absolute",
                  left: `${beat.tactical_reticle.target_x_pct ?? 50}%`,
                  top: `${beat.tactical_reticle.target_y_pct ?? 45}%`,
                  transform: `translate(-50%, -50%) scale(${interpolate(accentIn, [0, 1], [1.25, 1.0])})`,
                  opacity: accentIn,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  pointerEvents: "none",
                }}
              >
                {shared.reticle_circle ? (
                  <Img
                    src={resolveDocSrc(shared.reticle_circle)}
                    style={{ width: 210, height: 210, objectFit: "contain" }}
                  />
                ) : (
                  <div
                    style={{
                      width: 190,
                      height: 190,
                      borderRadius: "50%",
                      border: "5px solid #D90429",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.45)",
                    }}
                  />
                )}
                {beat.tactical_reticle.label && (
                  <div
                    style={{
                      marginTop: 6,
                      backgroundColor: "#D90429",
                      color: "#FFFFFF",
                      fontFamily: "'IBM Plex Mono', monospace",
                      fontWeight: 600,
                      fontSize: 20,
                      padding: "4px 12px",
                      letterSpacing: "0.08em",
                    }}
                  >
                    {beat.tactical_reticle.label.toUpperCase()}
                  </div>
                )}
              </div>
            )}
          </div>

          {beat.sub_caption && (
            <div
              style={{
                marginTop: 18,
                fontFamily: "'Source Serif 4', serif",
                fontStyle: "italic",
                fontWeight: 700,
                fontSize: 30,
                color: "#E5DEC9",
                textAlign: "center",
              }}
            >
              {beat.sub_caption}
            </div>
          )}
        </div>
      )}

      {/* ===== LAYOUT 4: 2.5D ARTICULATED PUPPET CONFRONTATION ===== */}
      {beat.layout_style === "puppet_confrontation_25d" && (
        <div
          style={{
            position: "absolute",
            top: 410,
            left: 36,
            right: 36,
            bottom: 245,
            zIndex: 25,
          }}
        >
          {/* Animated Confrontation Phase Curve */}
          {(() => {
            const p1In = interpolate(frame, [10, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT_EXPO });
            const p2In = interpolate(frame, [18, 32], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_OUT_EXPO });
            const strikeStart = Math.floor(dur * 0.38);
            const lunge = interpolate(frame, [strikeStart, strikeStart + 10, strikeStart + 22], [0, 1, 0.3], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: EASE_OUT_EXPO,
            });
            const recoil = interpolate(frame, [strikeStart + 5, strikeStart + 16], [0, 1], {
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
                      left: 16,
                      bottom: 20,
                      width: 530,
                      height: 820,
                      opacity: p1In,
                      transformOrigin: "50% 85%",
                      transform: `translate3d(${(1 - p1In) * -140 + lunge * 54}px, ${cutFloatY}px, 0) rotate(${lunge * 7.5}deg)`,
                    }}
                  >
                    <Img
                      src={resolveDocSrc(beat.cutout.path)}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        filter: "drop-shadow(0 20px 28px rgba(0,0,0,0.75))",
                      }}
                    />
                  </div>
                )}

                {beat.secondary_cutout && (
                  <div
                    style={{
                      position: "absolute",
                      right: 16,
                      bottom: 20,
                      width: 530,
                      height: 820,
                      opacity: p2In,
                      transformOrigin: "50% 85%",
                      transform: `translate3d(${(1 - p2In) * 140 + recoil * 34}px, ${-cutFloatY}px, 0) rotate(${recoil * 9.5}deg)`,
                    }}
                  >
                    <Img
                      src={resolveDocSrc(beat.secondary_cutout.path)}
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        filter: "drop-shadow(0 20px 28px rgba(0,0,0,0.75))",
                      }}
                    />
                  </div>
                )}
              </>
            );
          })()}
        </div>
      )}

      {/* ===== LAYOUT 5: TACTILE CHRONOLOGICAL TIMELINE CARD ===== */}
      {beat.layout_style === "tactile_timeline_card" && (
        <div
          style={{
            position: "absolute",
            top: 430,
            left: 56,
            right: 56,
            bottom: 245,
            display: "flex",
            flexDirection: "row",
            alignItems: "flex-start",
            justifyContent: "space-between",
            zIndex: 26,
          }}
        >
          {/* Left Timeline Stack (No heavy rounded black rectangles — paper strips with crimson dates) */}
          <div style={{ width: beat.cutout ? "58%" : "100%", display: "flex", flexDirection: "column", gap: 24 }}>
            {(beat.timeline_items || []).map((item, idx) => {
              const itemDelay = 14 + idx * 14;
              const p = interpolate(frame, [itemDelay, itemDelay + 12], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: EASE_OUT_EXPO,
              });
              return (
                <div
                  key={idx}
                  style={{
                    opacity: p,
                    transform: `translateX(${(1 - p) * -45}px)`,
                    backgroundColor: "#F2EDE3",
                    borderLeft: "7px solid #D90429",
                    padding: "16px 22px",
                    boxShadow: "0 12px 24px rgba(0,0,0,0.5)",
                  }}
                >
                  <div
                    style={{
                      fontFamily: "'IBM Plex Mono', monospace",
                      fontWeight: 600,
                      fontSize: 22,
                      color: "#D90429",
                      letterSpacing: "0.08em",
                      marginBottom: 4,
                    }}
                  >
                    {item.year} // {item.event}
                  </div>
                  <div
                    style={{
                      fontFamily: "'IBM Plex Sans', sans-serif",
                      fontWeight: 700,
                      fontSize: 27,
                      color: "#12151A",
                    }}
                  >
                    {item.detail}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Cutout Portrait */}
          {beat.cutout && (
            <div
              style={{
                width: "40%",
                height: 760,
                opacity: heroIn,
                transform: `translate3d(${(1 - heroIn) * 50 + cutDriftX * 0.4}px, ${cutFloatY}px, 0)`,
              }}
            >
              <Img
                src={resolveDocSrc(beat.cutout.path)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                  filter: "drop-shadow(0 18px 28px rgba(0,0,0,0.75))",
                }}
              />
            </div>
          )}
        </div>
      )}

      {/* ===== LAYOUT 6: RESTRAINED FULL-BLEED EDITORIAL EPILOGUE ===== */}
      {beat.layout_style === "clean_editorial_epilogue" && (
        <AbsoluteFill style={{ zIndex: 22 }}>
          {beat.editorial && (
            <Img
              src={resolveDocSrc(beat.editorial.path)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: beat.editorial.framing_mode === "broadcast_card" ? "contain" : "cover",
                objectPosition: `${beat.editorial.focal_x ?? 50}% ${beat.editorial.focal_y ?? 30}%`,
                transformOrigin: `${beat.editorial.focal_x ?? 50}% ${beat.editorial.focal_y ?? 30}%`,
                transform: `scale(${bgScale})`,
                filter: "contrast(1.06) brightness(0.82) saturate(0.88)",
              }}
            />
          )}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "linear-gradient(180deg, rgba(14,16,22,0.55) 0%, rgba(14,16,22,0) 25%, rgba(14,16,22,0.2) 55%, rgba(14,16,22,0.92) 84%, #0E1016 100%)",
            }}
          />
          <div
            style={{
              position: "absolute",
              left: 64,
              right: 64,
              bottom: 270,
              opacity: heroIn,
              transform: `translateY(${(1 - heroIn) * 32}px)`,
            }}
          >
            <div
              style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontWeight: 600,
                fontSize: 22,
                letterSpacing: "0.14em",
                color: "#FFE042",
                marginBottom: 10,
              }}
            >
              {beat.visual_kicker}
            </div>
            <div
              style={{
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 800,
                fontSize: 74,
                lineHeight: 0.98,
                color: "#F7F4EC",
                marginBottom: 12,
              }}
            >
              {beat.visual_headline}
            </div>
            {beat.sub_caption && (
              <div
                style={{
                  fontFamily: "'Source Serif 4', serif",
                  fontStyle: "italic",
                  fontWeight: 700,
                  fontSize: 32,
                  color: "#E0D9C8",
                }}
              >
                {beat.sub_caption}
              </div>
            )}
          </div>
        </AbsoluteFill>
      )}

      {/* Optional Distressed Red Rubber Stamp (Slams cleanly onto upper/lower negative space) */}
      {beat.stamp_path && (
        (() => {
          const stStart = Math.max(36, Math.floor(dur * 0.56));
          const sp = spring({
            frame: Math.max(0, frame - stStart),
            fps,
            config: { damping: 12, mass: 0.6, stiffness: 150 },
          });
          const vis = frame >= stStart ? 1 : 0;
          const stScale = interpolate(sp, [0, 1], [1.45, 1.0]);
          const posTop =
            beat.layout_style === "newspaper_highlighter"
              ? 1005
              : beat.layout_style === "puppet_confrontation_25d"
                ? 425
                : 1295;
          const posLeft =
            beat.layout_style === "newspaper_highlighter"
              ? 76
              : beat.layout_style === "puppet_confrontation_25d"
                ? 345
                : 590;
          return (
            <div
              style={{
                position: "absolute",
                top: posTop,
                left: posLeft,
                opacity: vis,
                transform: `scale(${stScale})`,
                zIndex: 42,
                pointerEvents: "none",
              }}
            >
              <Img
                src={resolveDocSrc(beat.stamp_path)}
                style={{
                  width: 380,
                  height: "auto",
                  objectFit: "contain",
                  filter: "drop-shadow(0 6px 14px rgba(0,0,0,0.48))",
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
