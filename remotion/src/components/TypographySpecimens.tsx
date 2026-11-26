import React from "react";
import { staticFile } from "remotion";
import { tokens } from "../design/tokens";

const W = 1080;
const H = 1920;
const MARGIN_X = tokens.safeArea.left + 29; // 84px preferred safe margin

// Common styles
const baseContainerStyle: React.CSSProperties = {
  width: W,
  height: H,
  backgroundColor: tokens.colors.navyPrimary,
  position: "relative",
  overflow: "hidden",
  color: tokens.colors.textWhite,
};

// Reusable Top HUD
export const SpecimenHUD: React.FC<{ kicker: string; kickerColor?: string }> = ({
  kicker,
  kickerColor = tokens.colors.cyanTactical,
}) => (
  <div
    style={{
      position: "absolute",
      top: 100,
      left: MARGIN_X,
      right: MARGIN_X,
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      zIndex: 60,
    }}
  >
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <span
        style={{
          background: tokens.colors.redNews,
          color: tokens.colors.textWhite,
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.bold,
          fontSize: 22,
          padding: "2px 8px",
          borderRadius: 3,
        }}
      >
        30+
      </span>
      <span
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.bold,
          fontSize: 28,
          letterSpacing: "1px",
          textTransform: "uppercase",
        }}
      >
        30 FOOTBALL PLUS
      </span>
    </div>

    <div
      style={{
        background: tokens.colors.navyCard,
        padding: "8px 18px",
        borderRadius: 4,
        borderRight: `4px solid ${kickerColor}`,
        boxShadow: tokens.colors.shadowCard,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: kickerColor,
        }}
      />
      <span
        style={{
          fontFamily: tokens.typography.fontMono,
          fontWeight: tokens.typography.weights.semiBold,
          fontSize: tokens.typography.sizes.hudBadge,
          letterSpacing: tokens.typography.letterSpacing.wide,
          color: kickerColor,
          textTransform: "uppercase",
        }}
      >
        {kicker}
      </span>
    </div>
  </div>
);

// 1. Opening Headline Specimen
export const HeadlineSpecimen: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S01_approved_4205420c.png")}
      alt="Bernabeu"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.85) 0%, rgba(10,15,26,0.3) 40%, rgba(10,15,26,0.92) 100%)",
      }}
    />
    <SpecimenHUD kicker="TRANSFER WATCH" kickerColor={tokens.colors.cyanTactical} />

    {/* Primary Headline Box */}
    <div
      style={{
        position: "absolute",
        top: 260,
        left: MARGIN_X,
        right: MARGIN_X,
        zIndex: 40,
      }}
    >
      <div
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.extraBold,
          fontSize: tokens.typography.sizes.headlineLarge,
          lineHeight: tokens.typography.lineHeights.headline,
          letterSpacing: tokens.typography.letterSpacing.tight,
          textTransform: "uppercase",
          textShadow: "0 4px 20px rgba(0,0,0,0.9)",
          color: tokens.colors.textWhite,
        }}
      >
        MILAN PLOT JAN MOVE
        <br />
        MOURINHO RESISTS EXIT
      </div>

      <div
        style={{
          marginTop: 20,
          fontFamily: tokens.typography.fontReading,
          fontWeight: tokens.typography.weights.semiBold,
          fontSize: tokens.typography.sizes.subheadline,
          lineHeight: tokens.typography.lineHeights.subheadline,
          color: tokens.colors.textOffWhite,
          maxWidth: "880px",
          textShadow: "0 2px 10px rgba(0,0,0,0.9)",
        }}
      >
        Real Madrid manager insists Endrick remains part of squad plans despite Italian approach
      </div>
    </div>
  </div>
);

// 2. Player Reveal Specimen
export const PlayerRevealSpecimen: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S02_approved_9ae4d40a.png")}
      alt="Endrick Reveal"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.8) 0%, rgba(10,15,26,0.15) 35%, rgba(10,15,26,0.92) 80%)",
      }}
    />
    <SpecimenHUD kicker="SUBJECT REVEAL" kickerColor={tokens.colors.yellowHighlight} />

    {/* Player Reveal Card */}
    <div
      style={{
        position: "absolute",
        bottom: 240,
        left: MARGIN_X,
        right: MARGIN_X,
        background: tokens.colors.navyCard,
        borderLeft: `8px solid ${tokens.colors.yellowHighlight}`,
        borderRadius: "0 12px 12px 0",
        padding: "24px 32px",
        boxShadow: tokens.colors.shadowHeavy,
        zIndex: 40,
      }}
    >
      <div
        style={{
          fontFamily: tokens.typography.fontMono,
          fontWeight: tokens.typography.weights.semiBold,
          fontSize: 20,
          letterSpacing: "1.5px",
          color: tokens.colors.yellowHighlight,
          textTransform: "uppercase",
          marginBottom: 6,
        }}
      >
        ● FOCAL SUBJECT REVEAL
      </div>

      <div
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.extraBold,
          fontSize: tokens.typography.sizes.playerReveal,
          lineHeight: 0.95,
          letterSpacing: tokens.typography.letterSpacing.tight,
          textTransform: "uppercase",
          color: tokens.colors.yellowHighlight,
          textShadow: "0 4px 18px rgba(0,0,0,0.85)",
        }}
      >
        ENDRICK
      </div>

      <div
        style={{
          marginTop: 12,
          fontFamily: tokens.typography.fontReading,
          fontWeight: tokens.typography.weights.semiBold,
          fontSize: tokens.typography.sizes.subheadline,
          color: tokens.colors.textWhite,
        }}
      >
        Twenty-year-old forward previously explored by AC Milan
      </div>

      <div
        style={{
          marginTop: 10,
          fontFamily: tokens.typography.fontMono,
          fontWeight: tokens.typography.weights.medium,
          fontSize: tokens.typography.sizes.sourceMetadata,
          color: tokens.colors.textMuted,
        }}
      >
        BORN 2006-07-21 • REAL MADRID C.F. FIRST TEAM
      </div>
    </div>
  </div>
);

// 3A. Single-Line Narration Subtitle Specimen (Clean 1080x1920 Broadcast)
export const SingleLineSubtitleSpecimen: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S01_approved_4205420c.png")}
      alt="Bernabeu"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.85) 0%, rgba(10,15,26,0.2) 35%, rgba(10,15,26,0.94) 85%)",
      }}
    />
    <SpecimenHUD kicker="SUBTITLE TYPOGRAPHY" kickerColor={tokens.colors.cyanTactical} />

    {/* Single-line Subtitle at bottom safe area */}
    <div
      style={{
        position: "absolute",
        bottom: 220,
        left: MARGIN_X,
        right: MARGIN_X,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          background: "linear-gradient(180deg, rgba(11, 19, 43, 0) 0%, rgba(11, 19, 43, 0.88) 100%)",
          padding: "16px 36px",
          borderRadius: 8,
          textAlign: "center",
          maxWidth: "960px",
        }}
      >
        <span
          style={{
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.subtitleCard,
            lineHeight: tokens.typography.lineHeights.subtitle,
            color: tokens.colors.textWhite,
            textShadow: "0 2px 10px rgba(0,0,0,0.95)",
          }}
        >
          Milan are plotting a January approach, but José Mourinho refuses to let him leave.
        </span>
      </div>
    </div>
  </div>
);

// 3B. Two-Line Narration Subtitle Specimen (Clean 1080x1920 Broadcast)
export const TwoLineSubtitleSpecimen: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S04_approved_9b1f2779.png")}
      alt="Training"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.85) 0%, rgba(10,15,26,0.2) 35%, rgba(10,15,26,0.95) 85%)",
      }}
    />
    <SpecimenHUD kicker="SUBTITLE TYPOGRAPHY" kickerColor={tokens.colors.yellowHighlight} />

    {/* Two-line Subtitle at bottom safe area */}
    <div
      style={{
        position: "absolute",
        bottom: 220,
        left: MARGIN_X,
        right: MARGIN_X,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          background: "linear-gradient(180deg, rgba(11, 19, 43, 0) 0%, rgba(11, 19, 43, 0.88) 100%)",
          padding: "16px 36px",
          borderRadius: 8,
          textAlign: "center",
          maxWidth: "960px",
        }}
      >
        <span
          style={{
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.subtitleCard,
            lineHeight: tokens.typography.lineHeights.subtitle,
            color: tokens.colors.textWhite,
            textShadow: "0 2px 12px rgba(0,0,0,0.95)",
          }}
        >
          Italian reports link twenty-year-old Endrick
          <br />
          to sixty million fixed, plus ten in bonuses.
        </span>
      </div>
    </div>
  </div>
);

// 3. Narration Subtitle Specimen (Legacy alias pointing to TwoLineSubtitleSpecimen)
export const SubtitleSpecimen: React.FC = TwoLineSubtitleSpecimen;

// 4. Transfer Graphic Specimen
export const TransferGraphicSpecimen: React.FC = () => (
  <div style={{ ...baseContainerStyle, backgroundColor: "#0A0F1A" }}>
    <SpecimenHUD kicker="DEAL STRUCTURE" kickerColor={tokens.colors.cyanTactical} />

    <div
      style={{
        position: "absolute",
        top: 240,
        left: MARGIN_X,
        right: MARGIN_X,
        bottom: 240,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <div>
        <div
          style={{
            fontFamily: tokens.typography.fontDisplay,
            fontWeight: tokens.typography.weights.extraBold,
            fontSize: 56,
            textTransform: "uppercase",
            color: tokens.colors.textWhite,
          }}
        >
          ENDRICK TRANSFER PROPOSAL
        </div>
        <div
          style={{
            marginTop: 8,
            fontFamily: tokens.typography.fontMono,
            fontWeight: tokens.typography.weights.medium,
            fontSize: 22,
            color: tokens.colors.textMuted,
          }}
        >
          ITALIAN PRESS FIGURES REPORTED • UNFORMALIZED TERMS
        </div>
      </div>

      {/* Block 1: Base Proposal + Bonuses */}
      <div
        style={{
          background: tokens.colors.navyCard,
          border: `2px solid ${tokens.colors.navyAccent}`,
          borderRadius: 16,
          padding: "24px 32px",
        }}
      >
        <div
          style={{
            fontFamily: tokens.typography.fontMono,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.statisticLabel,
            color: tokens.colors.cyanTactical,
            textTransform: "uppercase",
            marginBottom: 8,
          }}
        >
          AC MILAN • PREVIOUSLY EXPLORED PROPOSAL
        </div>
        <div
          style={{
            fontFamily: tokens.typography.fontDisplay,
            fontWeight: tokens.typography.weights.extraBold,
            fontSize: tokens.typography.sizes.statisticHero,
            lineHeight: 0.92,
            color: tokens.colors.cyanTactical,
          }}
        >
          €60M FIXED
        </div>
        <div
          style={{
            marginTop: 8,
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: 24,
            color: tokens.colors.textOffWhite,
          }}
        >
          + €10M in potential bonuses (unconfirmed)
        </div>
      </div>

      {/* Relationship Indicator */}
      <div style={{ textAlign: "center" }}>
        <span
          style={{
            fontFamily: tokens.typography.fontDisplay,
            fontWeight: tokens.typography.weights.bold,
            fontSize: 30,
            letterSpacing: "2px",
            color: tokens.colors.textWhite,
            background: "#16233B",
            padding: "8px 24px",
            borderRadius: 20,
            border: "1px solid #38BDF8",
          }}
        >
          ▲ REPURCHASE MECHANISM ▼
        </span>
      </div>

      {/* Block 2: Buy-back parameters */}
      <div
        style={{
          background: tokens.colors.navyCard,
          border: `2px solid ${tokens.colors.navyAccent}`,
          borderRadius: 16,
          padding: "24px 32px",
        }}
      >
        <div
          style={{
            fontFamily: tokens.typography.fontMono,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.statisticLabel,
            color: tokens.colors.yellowHighlight,
            textTransform: "uppercase",
            marginBottom: 8,
          }}
        >
          REAL MADRID • REPORTED BUY-BACK PROTECTION
        </div>
        <div
          style={{
            fontFamily: tokens.typography.fontDisplay,
            fontWeight: tokens.typography.weights.extraBold,
            fontSize: 104,
            lineHeight: 0.92,
            color: tokens.colors.yellowHighlight,
          }}
        >
          €80M – €85M
        </div>
        <div
          style={{
            marginTop: 8,
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: 24,
            color: "#FDE68A",
          }}
        >
          Attributed range • Never finalized or agreed
        </div>
      </div>

      {/* Prominent NOT AGREED Banner */}
      <div
        style={{
          background: "#321014",
          border: `3px solid ${tokens.colors.redNews}`,
          borderRadius: 14,
          padding: "20px 24px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontFamily: tokens.typography.fontMono,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: 34,
            color: "#FECACA",
          }}
        >
          ● STATUS: NOT AGREED
        </div>
        <div
          style={{
            marginTop: 6,
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.regular,
            fontSize: 22,
            color: "#FCA5A5",
          }}
        >
          Historical inquiry prior to Nov 23 medical update • Terms unformalized
        </div>
      </div>
    </div>
  </div>
);

// 5. Lower-Third Specimen
export const LowerThirdSpecimen: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S04_approved_9b1f2779.png")}
      alt="Endrick Training"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.8) 0%, rgba(10,15,26,0.2) 40%, rgba(10,15,26,0.95) 85%)",
      }}
    />
    <SpecimenHUD kicker="SQUAD REPORT" kickerColor={tokens.colors.cyanTactical} />

    {/* Broadcast Lower-Third Component */}
    <div
      style={{
        position: "absolute",
        bottom: 240,
        left: MARGIN_X,
        right: MARGIN_X,
        background: tokens.colors.navyCard,
        borderLeft: `8px solid ${tokens.colors.redNews}`,
        borderRadius: "0 10px 10px 0",
        padding: "22px 28px",
        boxShadow: tokens.colors.shadowHeavy,
        zIndex: 40,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
        <span
          style={{
            background: tokens.colors.cyanTactical,
            color: tokens.colors.navyPrimary,
            fontFamily: tokens.typography.fontMono,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.hudBadge,
            padding: "3px 10px",
            borderRadius: 4,
            textTransform: "uppercase",
          }}
        >
          ● SERIE A INQUIRIES
        </span>

        <span
          style={{
            background: tokens.colors.yellowHighlight,
            color: tokens.colors.navyPrimary,
            fontFamily: tokens.typography.fontMono,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.hudBadge,
            padding: "3px 10px",
            borderRadius: 4,
            textTransform: "uppercase",
          }}
        >
          STATUS: REPORTED
        </span>

        <span
          style={{
            color: tokens.colors.textMuted,
            fontFamily: tokens.typography.fontMono,
            fontSize: tokens.typography.sizes.sourceMetadata,
            marginLeft: "auto",
          }}
        >
          SRC: THE ATHLETIC / REUTERS
        </span>
      </div>

      <div
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.extraBold,
          fontSize: 68,
          lineHeight: tokens.typography.lineHeights.headline,
          letterSpacing: tokens.typography.letterSpacing.tight,
          textTransform: "uppercase",
          color: tokens.colors.textWhite,
        }}
      >
        MADRID DEMAND BUY-BACK CLAUSE BEFORE TALKS
      </div>

      <div
        style={{
          marginTop: 10,
          fontFamily: tokens.typography.fontReading,
          fontWeight: tokens.typography.weights.semiBold,
          fontSize: tokens.typography.sizes.subheadline,
          color: tokens.colors.yellowHighlight,
        }}
      >
        Italian press reports unformalized parameters between clubs
      </div>
    </div>
  </div>
);

// 6. Outro Specimen
export const OutroSpecimen: React.FC = () => (
  <div style={baseContainerStyle}>
    {/* Outro Spotlight & Ambient depth */}
    <div
      style={{
        position: "absolute",
        top: 250,
        left: "50%",
        transform: "translateX(-50%)",
        width: 900,
        height: 900,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(30,70,180,0.45) 0%, rgba(10,15,26,0) 70%)",
      }}
    />

    <div
      style={{
        position: "absolute",
        top: "40%",
        left: MARGIN_X,
        right: MARGIN_X,
        transform: "translateY(-50%)",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 140,
          height: 140,
          margin: "0 auto 30px",
          background: tokens.colors.redNews,
          borderRadius: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 12px 35px rgba(217, 4, 41, 0.4)",
        }}
      >
        <span
          style={{
            fontFamily: tokens.typography.fontDisplay,
            fontWeight: tokens.typography.weights.black,
            fontSize: 72,
            color: tokens.colors.textWhite,
          }}
        >
          30+
        </span>
      </div>

      <div
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.bold,
          fontSize: tokens.typography.sizes.outroHeadline,
          letterSpacing: "2px",
          textTransform: "uppercase",
          color: tokens.colors.textWhite,
        }}
      >
        30 FOOTBALL PLUS
      </div>

      <div
        style={{
          marginTop: 16,
          fontFamily: tokens.typography.fontReading,
          fontWeight: tokens.typography.weights.semiBold,
          fontSize: tokens.typography.sizes.outroCTA,
          color: tokens.colors.textMuted,
          letterSpacing: "1px",
        }}
      >
        BROADCAST FOOTBALL INTELLIGENCE
      </div>

      <div style={{ marginTop: 40 }}>
        <span
          style={{
            background: tokens.colors.yellowHighlight,
            color: tokens.colors.navyPrimary,
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.bold,
            fontSize: 26,
            padding: "14px 36px",
            borderRadius: 30,
            letterSpacing: "0.5px",
            boxShadow: tokens.colors.shadowGlowYellow,
          }}
        >
          FOLLOW FOR DAILY VERIFIED REPORTS
        </span>
      </div>
    </div>
  </div>
);

// 7. Portuguese (PT-BR) Specimen
export const PtBrSpecimen: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S02_approved_9ae4d40a.png")}
      alt="Endrick"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.88) 0%, rgba(10,15,26,0.2) 35%, rgba(10,15,26,0.96) 78%)",
      }}
    />
    <SpecimenHUD kicker="MERCADO DA BOLA" kickerColor={tokens.colors.cyanTactical} />

    {/* Portuguese Headline */}
    <div style={{ position: "absolute", top: 250, left: MARGIN_X, right: MARGIN_X }}>
      <div
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.extraBold,
          fontSize: 70,
          lineHeight: tokens.typography.lineHeights.headline,
          letterSpacing: tokens.typography.letterSpacing.tight,
          textTransform: "uppercase",
          textShadow: "0 4px 18px rgba(0,0,0,0.9)",
        }}
      >
        PROPOSTA POR ENDRICK AVANÇA
        <br />
        COM PROTEÇÃO DO REAL MADRID
      </div>
    </div>

    {/* Portuguese Lower Third & Subtitle */}
    <div style={{ position: "absolute", bottom: 180, left: MARGIN_X, right: MARGIN_X }}>
      {/* Subtitle */}
      <div
        style={{
          background: "linear-gradient(180deg, rgba(11, 19, 43, 0) 0%, rgba(11, 19, 43, 0.88) 100%)",
          padding: "16px 28px",
          borderRadius: 8,
          textAlign: "center",
          marginBottom: 30,
        }}
      >
        <span
          style={{
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.subtitleCard,
            lineHeight: tokens.typography.lineHeights.subtitle,
            color: tokens.colors.textWhite,
            textShadow: "0 2px 10px rgba(0,0,0,0.95)",
          }}
        >
          O Milan estuda investida ambiciosa pelo atacante de vinte anos, mas espanhóis exigem recompra.
        </span>
      </div>

      {/* Info Card */}
      <div
        style={{
          background: tokens.colors.navyCard,
          borderLeft: `8px solid ${tokens.colors.yellowHighlight}`,
          borderRadius: "0 8px 8px 0",
          padding: "18px 24px",
          boxShadow: tokens.colors.shadowHeavy,
        }}
      >
        <div style={{ fontFamily: tokens.typography.fontMono, fontSize: 18, color: tokens.colors.yellowHighlight, marginBottom: 4 }}>
          ● ATUALIZAÇÃO MÉDICA
        </div>
        <div style={{ fontFamily: tokens.typography.fontReading, fontWeight: tokens.typography.weights.semiBold, fontSize: 32, color: tokens.colors.textWhite }}>
          Lesão no adutor da perna esquerda adiciona incerteza à temporada
        </div>
      </div>
    </div>
  </div>
);

// 8. Spanish (ES-419) Specimen
export const Es419Specimen: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S02_approved_9ae4d40a.png")}
      alt="Endrick"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.88) 0%, rgba(10,15,26,0.2) 35%, rgba(10,15,26,0.96) 78%)",
      }}
    />
    <SpecimenHUD kicker="FICHAJES AL DÍA" kickerColor={tokens.colors.cyanTactical} />

    {/* Spanish Headline */}
    <div style={{ position: "absolute", top: 250, left: MARGIN_X, right: MARGIN_X }}>
      <div
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.extraBold,
          fontSize: 68,
          lineHeight: tokens.typography.lineHeights.headline,
          letterSpacing: tokens.typography.letterSpacing.tight,
          textTransform: "uppercase",
          textShadow: "0 4px 18px rgba(0,0,0,0.9)",
        }}
      >
        EL MILAN PREPARA OFERTA POR ENDRICK
        <br />
        CON CLÁUSULA BLINDADA
      </div>
    </div>

    {/* Spanish Lower Third & Subtitle */}
    <div style={{ position: "absolute", bottom: 180, left: MARGIN_X, right: MARGIN_X }}>
      {/* Subtitle */}
      <div
        style={{
          background: "linear-gradient(180deg, rgba(11, 19, 43, 0) 0%, rgba(11, 19, 43, 0.88) 100%)",
          padding: "16px 28px",
          borderRadius: 8,
          textAlign: "center",
          marginBottom: 30,
        }}
      >
        <span
          style={{
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.subtitleCard,
            lineHeight: tokens.typography.lineHeights.subtitle,
            color: tokens.colors.textWhite,
            textShadow: "0 2px 10px rgba(0,0,0,0.95)",
          }}
        >
          El club italiano sondea la cesión del atacante de veinte años, mientras el Madrid exige una opción de retorno.
        </span>
      </div>

      {/* Info Card */}
      <div
        style={{
          background: tokens.colors.navyCard,
          borderLeft: `8px solid ${tokens.colors.yellowHighlight}`,
          borderRadius: "0 8px 8px 0",
          padding: "18px 24px",
          boxShadow: tokens.colors.shadowHeavy,
        }}
      >
        <div style={{ fontFamily: tokens.typography.fontMono, fontSize: 18, color: tokens.colors.yellowHighlight, marginBottom: 4 }}>
          ● PARTE MÉDICO OFICIAL
        </div>
        <div style={{ fontFamily: tokens.typography.fontReading, fontWeight: tokens.typography.weights.semiBold, fontSize: 30, color: tokens.colors.textWhite }}>
          Parte médico confirma lesión en el aductor de la pierna izquierda pendiente de evolución
        </div>
      </div>
    </div>
  </div>
);

// 9. Master Typography Clean Composition
export const TypographyMasterClean: React.FC = () => (
  <div style={baseContainerStyle}>
    <img
      src={staticFile("images/S01_approved_4205420c.png")}
      alt="Bernabeu"
      style={{ width: W, height: H, objectFit: "cover", position: "absolute", top: 0, left: 0 }}
    />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "linear-gradient(180deg, rgba(10,15,26,0.85) 0%, rgba(10,15,26,0.3) 30%, rgba(10,15,26,0.95) 75%)",
      }}
    />
    <SpecimenHUD kicker="TRANSFER WATCH" kickerColor={tokens.colors.cyanTactical} />

    {/* Primary Headline */}
    <div style={{ position: "absolute", top: 250, left: MARGIN_X, right: MARGIN_X }}>
      <div
        style={{
          fontFamily: tokens.typography.fontDisplay,
          fontWeight: tokens.typography.weights.extraBold,
          fontSize: tokens.typography.sizes.headlineLarge,
          lineHeight: tokens.typography.lineHeights.headline,
          letterSpacing: tokens.typography.letterSpacing.tight,
          textTransform: "uppercase",
          textShadow: "0 4px 20px rgba(0,0,0,0.9)",
        }}
      >
        ENDRICK TRANSFER PROPOSAL
        <br />
        ADVANCES IN ITALY
      </div>
    </div>

    {/* Central Data Card */}
    <div
      style={{
        position: "absolute",
        top: 550,
        left: MARGIN_X,
        right: MARGIN_X,
        background: tokens.colors.navyCard,
        borderRadius: 16,
        padding: "24px 30px",
        border: `2px solid ${tokens.colors.navyAccent}`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontFamily: tokens.typography.fontMono, fontSize: 20, color: tokens.colors.cyanTactical }}>
            REPORTED BASE BID
          </div>
          <div style={{ fontFamily: tokens.typography.fontDisplay, fontWeight: 800, fontSize: 110, color: tokens.colors.cyanTactical, lineHeight: 0.95 }}>
            €60M
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontFamily: tokens.typography.fontMono, fontSize: 20, color: tokens.colors.yellowHighlight }}>
            BUY-BACK RANGE
          </div>
          <div style={{ fontFamily: tokens.typography.fontDisplay, fontWeight: 800, fontSize: 72, color: tokens.colors.yellowHighlight, lineHeight: 0.95 }}>
            €80M–€85M
          </div>
        </div>
      </div>
      <div
        style={{
          marginTop: 16,
          background: "#321014",
          border: `1px solid ${tokens.colors.redNews}`,
          padding: "8px 16px",
          borderRadius: 6,
          textAlign: "center",
          fontFamily: tokens.typography.fontMono,
          fontSize: 20,
          color: "#FECACA",
        }}
      >
        ● STATUS: NOT AGREED • TERMS UNFORMALIZED
      </div>
    </div>

    {/* Narration Subtitle */}
    <div style={{ position: "absolute", bottom: 220, left: MARGIN_X, right: MARGIN_X, textAlign: "center" }}>
      <div
        style={{
          background: "linear-gradient(180deg, rgba(11, 19, 43, 0) 0%, rgba(11, 19, 43, 0.88) 100%)",
          padding: "16px 28px",
          borderRadius: 8,
          display: "inline-block",
          maxWidth: "920px",
        }}
      >
        <span
          style={{
            fontFamily: tokens.typography.fontReading,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: tokens.typography.sizes.subtitleCard,
            lineHeight: tokens.typography.lineHeights.subtitle,
            color: tokens.colors.textWhite,
            textShadow: "0 2px 10px rgba(0,0,0,0.95)",
          }}
        >
          Milan are targeting Endrick, exploring an ambitious move for the twenty-year-old forward.
        </span>
      </div>
    </div>
  </div>
);

// 10. Master Typography Diagnostic Composition
export const TypographyDiagnostic: React.FC = () => (
  <div style={baseContainerStyle}>
    <TypographyMasterClean />

    {/* Safe Zone Margin Lines */}
    <div style={{ position: "absolute", top: 0, bottom: 0, left: MARGIN_X, width: 1, background: "rgba(56,189,248,0.5)" }} />
    <div style={{ position: "absolute", top: 0, bottom: 0, right: MARGIN_X, width: 1, background: "rgba(56,189,248,0.5)" }} />
    <div style={{ position: "absolute", left: 0, right: 0, top: 1640, height: 2, background: "rgba(239,68,68,0.7)" }} />

    {/* Diagnostic Overlays */}
    <div
      style={{
        position: "absolute",
        top: 220,
        left: MARGIN_X,
        background: "rgba(0,0,0,0.75)",
        padding: "4px 10px",
        borderRadius: 4,
        fontFamily: tokens.typography.fontMono,
        fontSize: 16,
        color: tokens.colors.cyanTactical,
      }}
    >
      Headline: Barlow Condensed ExtraBold 78px / LH 0.98
    </div>

    <div
      style={{
        position: "absolute",
        top: 515,
        left: MARGIN_X,
        background: "rgba(0,0,0,0.75)",
        padding: "4px 10px",
        borderRadius: 4,
        fontFamily: tokens.typography.fontMono,
        fontSize: 16,
        color: tokens.colors.cyanTactical,
      }}
    >
      Data Hero: Barlow Condensed 110px | Label: IBM Plex Mono 20px
    </div>

    <div
      style={{
        position: "absolute",
        bottom: 290,
        left: MARGIN_X,
        background: "rgba(0,0,0,0.75)",
        padding: "4px 10px",
        borderRadius: 4,
        fontFamily: tokens.typography.fontMono,
        fontSize: 16,
        color: tokens.colors.yellowHighlight,
      }}
    >
      Subtitles: Inter SemiBold 46px / LH 1.16 / Sentence Case
    </div>

    <div
      style={{
        position: "absolute",
        top: 1645,
        left: MARGIN_X,
        fontFamily: tokens.typography.fontMono,
        fontSize: 16,
        color: tokens.colors.redNews,
      }}
    >
      ▲ CRITICAL SAFE ZONE LIMIT (Avoid primary text below y=1640) ▲
    </div>
  </div>
);
