import sys
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from stages.image_sourcing import source_scene_image, reset_image_registry

reset_image_registry()

print("Testing dynamic image sourcing for Calvin Bassey / Man Utd...")
res1 = source_scene_image(
    scene_id=1,
    headline="Man Utd transfer news: Fulham defender Calvin Bassey is in talks over new contract amid Man Utd links",
    scene_text="Manchester United are monitoring Calvin Bassey as Fulham open contract talks.",
    visual_prompt="Calvin Bassey Fulham match action",
    source_name="Sky Sports",
    search_entity="Calvin Bassey",
    search_context="Fulham defender match action"
)
print("Chosen image 1:", res1.get("chosen_image"))

res2 = source_scene_image(
    scene_id=2,
    headline="Man Utd transfer news: Fulham defender Calvin Bassey is in talks over new contract amid Man Utd links",
    scene_text="Old Trafford executives are preparing a formal proposal.",
    visual_prompt="Old Trafford stadium night",
    source_name="Sky Sports",
    search_entity="Old Trafford stadium",
    search_context="Manchester United stadium night"
)
print("Chosen image 2:", res2.get("chosen_image"))
