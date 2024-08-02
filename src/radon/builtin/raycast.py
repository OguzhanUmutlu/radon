import json
from typing import List

from ..cpl._base import CompileTimeValue
from ..cpl.int import CplInt
from ..cpl.string import CplString
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib
from ..utils import get_expr_id


def get_fn_or_none(ctx, arr, index, token):
    if len(arr) <= index:
        return None
    if isinstance(arr[index], CplString):
        return ctx.transpiler.get_fn(arr[index].value, [], token).file_name
    return None


def lib_raycast(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    ctx.transpiler.dp_files[f"tags/block{ctx.transpiler.s}/__raycast__/default_raycast_pass.json"] = json.dumps({
        "values": [
            "minecraft:short_grass" if ctx.transpiler.pack_format >= 48 else "minecraft:grass",
            "minecraft:air",
            "minecraft:void_air",
            "minecraft:cave_air",
            "minecraft:water",
            "minecraft:lava",
            "#minecraft:small_flowers",
            "#minecraft:tall_flowers",
            "#minecraft:small_dripleaf_placeable",
            "minecraft:fern",
            "minecraft:fire",
            "minecraft:tall_grass",
            "minecraft:large_fern",
            "minecraft:vine",
            "minecraft:twisting_vines",
            "minecraft:twisting_vines_plant",
            "minecraft:weeping_vines",
            "minecraft:weeping_vines_plant",
            "#minecraft:crops",
            "#minecraft:saplings",
            "#minecraft:signs",
            "minecraft:attached_melon_stem",
            "minecraft:attached_pumpkin_stem",
            "minecraft:nether_wart",
            "minecraft:sweet_berry_bush",
            "minecraft:cocoa",
            "minecraft:sugar_cane",
            "minecraft:seagrass",
            "minecraft:tall_seagrass",
            "minecraft:redstone_wire",
            "minecraft:rail",
            "minecraft:powered_rail",
            "minecraft:activator_rail",
            "minecraft:detector_rail",
            "minecraft:torch",
            "minecraft:soul_torch",
            "minecraft:redstone_torch",
            "minecraft:glow_lichen"
        ]
    })
    raycast_id = get_expr_id()
    iter_eid = f"int_{raycast_id} __temp__"
    stop_iter = f"scoreboard players set {iter_eid} -1"
    ns = ctx.transpiler.pack_namespace
    hit_entity = get_fn_or_none(ctx, args, 0, token)
    hit_block = get_fn_or_none(ctx, args, 1, token)
    run_hit_entity = f"function {ns}:__raycast__/{raycast_id}/collide_entity" if hit_entity else stop_iter
    run_hit_block = f"function {ns}:__raycast__/{raycast_id}/collide_block" if hit_block else stop_iter

    ctx.file.extend([
        "tag @s add __raycast__self__",
        f"scoreboard players set {iter_eid} 1000",
        f"execute anchored eyes positioned ^ ^ ^0.1 run function {ns}:__raycast__/{raycast_id}/loop",
        "tag @s remove __raycast__self__"
    ])
    ctx.transpiler.files[f"__raycast__/{raycast_id}/loop"] = [
        f"execute positioned ~-0.95 ~-0.95 ~-0.95 as @e[dx=0,tag=!__raycast__self__] positioned ~0.9 ~0.9 ~0.9 if entity @s[dx=0] positioned ~0.05 ~0.05 ~0.05 run {run_hit_entity}",
        f"execute if score {iter_eid} matches 1.. run scoreboard players remove {iter_eid} 1",
        f"execute unless block ~ ~ ~ #{ns}:__raycast__/default_raycast_pass run {run_hit_block}",
        f"execute if score {iter_eid} matches 1.. positioned ^ ^ ^0.1 run function {ns}:__raycast__/{raycast_id}/loop"
    ]
    if hit_entity:
        ctx.transpiler.files[f"__raycast__/{raycast_id}/collide_entity"] = [
            stop_iter,
            f"function {ns}:{hit_entity}"
        ]
    if hit_block:
        ctx.transpiler.files[f"__raycast__/{raycast_id}/collide_block"] = [
            stop_iter,
            f"function {ns}:{hit_block}"
        ]
    return CplInt(token, 0)


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="raycast",
    function=lib_raycast
))
