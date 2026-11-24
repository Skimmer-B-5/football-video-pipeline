import React from "react";
import { Composition, staticFile } from "remotion";
import { FootballShort } from "./FootballShort";
import { FootballShortProps } from "./types";
import { tokens } from "./design/tokens";

const fontStyles = `
@font-face {
  font-family: 'Barlow Condensed';
  src: url('${staticFile("fonts/barlow_condensed/BarlowCondensed-SemiBold.ttf")}') format('truetype');
  font-weight: 600;
  font-style: normal;
}
@font-face {
  font-family: 'Barlow Condensed';
  src: url('${staticFile("fonts/barlow_condensed/BarlowCondensed-Bold.ttf")}') format('truetype');
  font-weight: 700;
  font-style: normal;
}
@font-face {
  font-family: 'Barlow Condensed';
  src: url('${staticFile("fonts/barlow_condensed/BarlowCondensed-ExtraBold.ttf")}') format('truetype');
  font-weight: 800;
  font-style: normal;
}
@font-face {
  font-family: 'Barlow Condensed';
  src: url('${staticFile("fonts/barlow_condensed/BarlowCondensed-Black.ttf")}') format('truetype');
  font-weight: 900;
  font-style: normal;
}

@font-face {
  font-family: 'Inter';
  src: url('${staticFile("fonts/inter/Inter-Regular.ttf")}') format('truetype');
  font-weight: 400;
  font-style: normal;
}
@font-face {
  font-family: 'Inter';
  src: url('${staticFile("fonts/inter/Inter-Medium.ttf")}') format('truetype');
  font-weight: 500;
  font-style: normal;
}
@font-face {
  font-family: 'Inter';
  src: url('${staticFile("fonts/inter/Inter-SemiBold.ttf")}') format('truetype');
  font-weight: 600;
  font-style: normal;
}
@font-face {
  font-family: 'Inter';
  src: url('${staticFile("fonts/inter/Inter-Bold.ttf")}') format('truetype');
  font-weight: 700;
  font-style: normal;
}
@font-face {
  font-family: 'Inter';
  src: url('${staticFile("fonts/inter/Inter-ExtraBold.ttf")}') format('truetype');
  font-weight: 800;
  font-style: normal;
}

@font-face {
  font-family: 'IBM Plex Mono';
  src: url('${staticFile("fonts/ibm_plex_mono/IBMPlexMono-Medium.ttf")}') format('truetype');
  font-weight: 500;
  font-style: normal;
}
@font-face {
  font-family: 'IBM Plex Mono';
  src: url('${staticFile("fonts/ibm_plex_mono/IBMPlexMono-SemiBold.ttf")}') format('truetype');
  font-weight: 600;
  font-style: normal;
}
`;

import {
  HeadlineSpecimen,
  PlayerRevealSpecimen,
  SubtitleSpecimen,
  SingleLineSubtitleSpecimen,
  TwoLineSubtitleSpecimen,
  TransferGraphicSpecimen,
  LowerThirdSpecimen,
  OutroSpecimen,
  PtBrSpecimen,
  Es419Specimen,
  TypographyMasterClean,
  TypographyDiagnostic,
} from "./components/TypographySpecimens";

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
      <style dangerouslySetInnerHTML={{ __html: fontStyles }} />
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
      {/* V7.1.4 / V7.1.5 Typography Specimen Compositions */}
      <Composition id="HeadlineSpecimen" component={HeadlineSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="PlayerRevealSpecimen" component={PlayerRevealSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="SubtitleSpecimen" component={SubtitleSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="SingleLineSubtitleSpecimen" component={SingleLineSubtitleSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="TwoLineSubtitleSpecimen" component={TwoLineSubtitleSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="TransferGraphicSpecimen" component={TransferGraphicSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="LowerThirdSpecimen" component={LowerThirdSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="OutroSpecimen" component={OutroSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="PtBrSpecimen" component={PtBrSpecimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="Es419Specimen" component={Es419Specimen} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="TypographyMasterClean" component={TypographyMasterClean} durationInFrames={30} fps={30} width={1080} height={1920} />
      <Composition id="TypographyDiagnostic" component={TypographyDiagnostic} durationInFrames={30} fps={30} width={1080} height={1920} />
    </>
  );
};
