import React from "react";
import { Series, Sequence, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { FootballShortProps } from "./types";
import { TopHUD } from "./components/TopHUD";
import { BackgroundMedia } from "./components/BackgroundMedia";
import { LowerThird } from "./components/LowerThird";
import { ContractExplainer } from "./components/ContractExplainer";
import { SubtitleCard } from "./components/SubtitleCard";
import { RollingTicker } from "./components/RollingTicker";
import { RetroOverlay } from "./components/RetroOverlay";
import { OutroPlate } from "./components/OutroPlate";

export const FootballShort: React.FC<FootballShortProps> = ({
  headline,
  scenes = [],
  tickerText,
  subtitles = [],
  kicker = "TRANSFER WATCH",
  logoSrc,
  masterLogoSrc,
  tickerBaseSrc,
  scanlinesSrc,
  enableRetroEffects = true,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Find if an explicit outro scene exists
  const outroScene = scenes.find((s) => s.scene_id === "outro");
  const outroDurationFrames = outroScene ? outroScene.durationInFrames : 45;
  const outroStartFrame = Math.max(0, durationInFrames - outroDurationFrames);
  const isOutroActive = frame >= outroStartFrame;

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
            {scene.scene_id === "outro" ? (
              <OutroPlate
                masterLogoSrc={masterLogoSrc}
                tickerBaseSrc={tickerBaseSrc}
              />
            ) : (
              <>
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
              </>
            )}
          </Series.Sequence>
        ))}
      </Series>

      {/* 2. Top HUD (Channel Bezel Bug & Truthful Status Kicker) - Hidden during outro */}
      {!isOutroActive && <TopHUD kicker={kicker} logoSrc={logoSrc} />}

      {/* 3. Subtitle Cards (Caption Zone) - Hidden during outro */}
      {!isOutroActive && <SubtitleCard subtitles={subtitles} />}

      {/* 4. Rolling Factual Ticker - Hidden during outro */}
      {!isOutroActive && <RollingTicker text={tickerText || headline} />}

      {/* 5. Authentic Retro 90s CRT Scanlines & Tube Vignette Overlay */}
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
