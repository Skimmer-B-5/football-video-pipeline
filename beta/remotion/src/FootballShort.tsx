import React from "react";
import { Series, useCurrentFrame, useVideoConfig } from "remotion";
import { FootballShortProps } from "./types";
import { TopHUD } from "./components/TopHUD";
import { BackgroundMedia } from "./components/BackgroundMedia";
import { LowerThird } from "./components/LowerThird";
import { InfographicDirector } from "./components/infographics/InfographicDirector";
import { SubtitleCard } from "./components/SubtitleCard";
import { RollingTicker } from "./components/RollingTicker";
import { RetroOverlay } from "./components/RetroOverlay";
import { OutroPlate } from "./components/OutroPlate";
import { tokens } from "./design/tokens";

export const FootballShort: React.FC<FootballShortProps> = ({
  headline,
  scenes = [],
  tickerText,
  subtitles = [],
  kicker = "TRANSFER WATCH",
  logoSrc,
  masterLogoSrc,
  tickerBaseSrc,
  headlinesTabSrc,
  scanlinesSrc,
  enableRetroEffects = true,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Find if an explicit outro scene exists
  const outroScene = scenes.find((s) => s.scene_id === "outro");
  const outroDurationFrames = outroScene ? outroScene.durationInFrames : tokens.animation.outroDurationFrames;
  const outroStartFrame = Math.max(0, durationInFrames - outroDurationFrames);
  const isOutroActive = frame >= outroStartFrame;

  return (
    <div
      style={{
        position: "relative",
        width: tokens.canvas.width,
        height: tokens.canvas.height,
        backgroundColor: tokens.colors.navyPrimary,
        overflow: "hidden",
        fontFamily: tokens.typography.fontPrimary,
      }}
    >
      {/* 1. Sequential Editorial Scenes */}
      <Series>
        {scenes.map((scene) => (
          <Series.Sequence
            key={scene.scene_id}
            durationInFrames={scene.durationInFrames}
          >
            {scene.scene_id === "outro" ? (
              <OutroPlate
                masterLogoSrc={masterLogoSrc}
                tickerBaseSrc={tickerBaseSrc}
                headlinesTabSrc={headlinesTabSrc}
                tickerText="FOLLOW FOR DAILY BREAKING NEWS ✦ EXCLUSIVE INTERVIEWS ✦ BREAKING TRANSFERS ✦"
              />
            ) : (
              <>
                {/* Full-Height Football Photography / Background Media */}
                <BackgroundMedia
                  imagePath={scene.image_path}
                  shots={scene.shots}
                  motion={scene.motion}
                  durationInFrames={scene.durationInFrames}
                />

                {/* Reusable Broadcast Lower-Third Headline Plate (Anchored at y: 1400) */}
                <LowerThird onScreen={scene.on_screen} />
              </>
            )}
          </Series.Sequence>
        ))}
      </Series>

      {/* 2. Top HUD (Channel Bezel Bug & Truthful Status Kicker) - Hidden during outro */}
      {!isOutroActive && <TopHUD kicker={kicker} logoSrc={logoSrc} />}

      {/* 3. Subtitle Cards (Caption Zone y: 1300) - Hidden during outro */}
      {!isOutroActive && <SubtitleCard subtitles={subtitles} />}

      {/* 4. Rolling Factual Ticker (Lowered to bottom: 90px, height: 110px) - Hidden during outro */}
      {!isOutroActive && (
        <RollingTicker
          text={tickerText || headline}
          tickerBaseSrc={tickerBaseSrc}
          headlinesTabSrc={headlinesTabSrc}
        />
      )}

      {/* 5. Authentic Retro 90s CRT Scanlines & Tube Layer */}
      {enableRetroEffects && (
        <RetroOverlay
          scanlinesSrc={scanlinesSrc}
          enableScanlines={true}
          enableVignette={true}
          enableFlicker={true}
        />
      )}
    </div>
  );
};
