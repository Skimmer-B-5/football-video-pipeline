import React from "react";
import { SceneVisual } from "../../types";
import { TransferFeeGraphic } from "./TransferFeeGraphic";
import { TransferRouteGraphic } from "./TransferRouteGraphic";
import { ContractClauseGraphic } from "./ContractClauseGraphic";
import { PlayerStatisticsGraphic } from "./PlayerStatisticsGraphic";
import { TacticalFormationGraphic } from "./TacticalFormationGraphic";
import { ClubComparisonGraphic } from "./ClubComparisonGraphic";
import { InjuryTimelineGraphic } from "./InjuryTimelineGraphic";
import { MatchStatisticsGraphic } from "./MatchStatisticsGraphic";
import { PlayerProfileGraphic } from "./PlayerProfileGraphic";

export interface InfographicDirectorProps {
  visual?: SceneVisual;
}

export const InfographicDirector: React.FC<InfographicDirectorProps> = ({ visual }) => {
  if (!visual || !visual.kind) return null;

  const kind = visual.kind.toLowerCase();
  const data = visual.infographic_data || {};

  switch (kind) {
    case "transfer_fee_graphic":
    case "fee_breakdown_graphic":
      return <TransferFeeGraphic {...data.transfer_fee} />;

    case "transfer_route_graphic":
    case "route_graphic":
      return <TransferRouteGraphic {...data.transfer_route} />;

    case "contract_or_clause_graphic":
    case "contract_clause_graphic":
    case "clause_graphic":
      return <ContractClauseGraphic {...data.contract_clause} />;

    case "player_statistics_graphic":
    case "stats_graphic":
      return <PlayerStatisticsGraphic {...data.player_statistics} />;

    case "tactical_formation_graphic":
    case "formation_graphic":
      return <TacticalFormationGraphic {...data.tactical_formation} />;

    case "club_comparison_graphic":
    case "comparison_graphic":
      return <ClubComparisonGraphic {...data.club_comparison} />;

    case "injury_timeline_graphic":
    case "injury_graphic":
      return <InjuryTimelineGraphic {...data.injury_timeline} />;

    case "match_statistics_graphic":
    case "match_result_graphic":
      return <MatchStatisticsGraphic {...data.match_statistics} />;

    case "player_profile_graphic":
    case "profile_graphic":
      return <PlayerProfileGraphic {...data.player_profile} />;

    default:
      return null;
  }
};
