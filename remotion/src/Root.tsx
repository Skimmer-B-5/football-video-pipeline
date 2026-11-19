import React from "react";
import { Composition } from "remotion";
import { FootballShort } from "./FootballShort";
import { FootballShortProps } from "./types";
import { tokens } from "./design/tokens";

const defaultProps: FootballShortProps = {
  story_id: "sample_short",
  headline: "Milan prepare €60m bid for Endrick",
  totalDurationInFrames: 1137, // ~37.9s @ 30fps
  kicker: "TRANSFER WATCH",
  tickerText: "CORRIERE DELLO SPORT: MILAN PREPARE €60M BID FOR ENDRICK ✦ €80M BUY-BACK CLAUSE REPORTED",
  scenes: [],
  subtitles: [],
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="FootballShort"
        component={FootballShort}
        durationInFrames={1137}
        fps={tokens.canvas.fps}
        width={tokens.canvas.width}
        height={tokens.canvas.height}
        defaultProps={defaultProps}
        calculateMetadata={({ props }) => {
          const typedProps = props as FootballShortProps;
          return {
            durationInFrames: Number(typedProps?.totalDurationInFrames) || 1137,
          };
        }}
      />
    </>
  );
};
