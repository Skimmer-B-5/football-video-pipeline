import React from "react";
import { Series, Sequence, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { FootballShortProps } from "./types";
import { TopHUD } from "./components/TopHUD";
import { BackgroundMedia } from "./components/BackgroundMedia";
import { LowerThird } from "./components/LowerThird";
import { ContractExplainer } from "./components/ContractExplainer";
import { SubtitleCard } from "./components/SubtitleCard";
import { RollingTicker } from "./components/RollingTicker";

export const FootballShort: React.FC<FootballShortProps> = ({
  headline,
  scenes = [],
  tickerText,
  subtitles = [],
  kicker = "TRANSFER WATCH",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Outro transition during final 40 frames (~1.33s)
  const outroStartFrame = Math.max(0, durationInFrames - 40);
  const isOutroActive = frame >= outroStartFrame;

  const outroSpring = spring({
    frame: frame - outroStartFrame,
    fps,
    config: { damping: 14, mass: 0.7, stiffness: 120 },
  });

  return (
    <div
      style={{
        position: "relative",
        width: 1080,
        height: 1920,
        backgroundColor: "#0B132B",
        overflow: "hidden",
        fontFamily: "'Barlow Condensed', sans-serif",
      }}
    >
      {/* 1. Sequential Editorial Scenes */}
      <Series>
        {scenes.map((scene) => (
          <Series.Sequence
            key={scene.scene_id}
            durationInFrames={scene.durationInFrames}
          >
            {/* Background Media */}
            <BackgroundMedia
              imagePath={scene.image_path}
              motion={scene.motion}
              durationInFrames={scene.durationInFrames}
            />

            {/* Special Contract Explainer Diagram */}
            {scene.visual?.kind === "contract_or_clause_graphic" && (
              <ContractExplainer />
            )}

            {/* Lower Third Headline Plate */}
            <LowerThird onScreen={scene.on_screen} />
          </Series.Sequence>
        ))}
      </Series>

      {/* 2. Top HUD (Channel Bug & Truthful Status Kicker) */}
      <TopHUD kicker={kicker} />

      {/* 3. Subtitle Cards (Caption Zone) */}
      <SubtitleCard subtitles={subtitles} />

      {/* 4. Rolling Factual Ticker */}
      <RollingTicker text={tickerText || headline} />

      {/* 5. Concise Integrated Outro Card (Final 1.33s) */}
      {isOutroActive && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(11, 19, 43, 0.94)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 60,
            opacity: Math.min(outroSpring * 1.2, 1),
          }}
        >
          <div
            style={{
              background: "#D90429",
              color: "#FFFFFF",
              fontFamily: "'Barlow Condensed', sans-serif",
              fontWeight: 900,
              fontSize: 64,
              padding: "8px 24px",
              borderRadius: 6,
              marginBottom: 16,
              transform: `scale(${0.9 + outroSpring * 0.1})`,
            }}
          >
            30s
          </div>
          <div
            style={{
              color: "#FFFFFF",
              fontFamily: "'Barlow Condensed', sans-serif",
              fontWeight: 900,
              fontSize: 52,
              letterSpacing: "3px",
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            FOOTBALL IN 30 SECONDS
          </div>
          <div
            style={{
              color: "#FFD166",
              fontFamily: "'Barlow Condensed', sans-serif",
              fontWeight: 700,
              fontSize: 34,
              letterSpacing: "2px",
              textTransform: "uppercase",
            }}
          >
            FOLLOW FOR DAILY TRANSFERS & TACTICS
          </div>
        </div>
      )}
    </div>
  );
};
