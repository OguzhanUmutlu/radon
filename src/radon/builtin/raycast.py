import json
from typing import List

from ..cpl._base import CompileTimeValue
from ..cpl.score import CplScore
from ..cpl.string import CplString
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib
from ..utils import get_uuid


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
    raycast_id = get_uuid()
    iter_eid = f"int_{raycast_id} __temp__"
    success_eid = f"int_raycast_success_{raycast_id} __temp__"
    stop_iter = f"scoreboard players set {iter_eid} -1"
    ns = ctx.transpiler.pack_namespace

    entity_fn = get_fn_or_none(ctx, args, 0, token)
    block_fn = get_fn_or_none(ctx, args, 1, token)
    step_fn = get_fn_or_none(ctx, args, 2, token)
    fail_fn = get_fn_or_none(ctx, args, 3, token)

    entity_file = f"__raycast__/{raycast_id}/collide_entity" if entity_fn else ""
    block_file = f"__raycast__/{raycast_id}/collide_block" if block_fn else ""
    fail_file = f"__raycast__/{raycast_id}/fail" if fail_fn else ""

    ctx.file.extend([
        f"scoreboard players set {success_eid} 1",
        "tag @s add __raycast__self__",
        f"scoreboard players set {iter_eid} 1000",
        f"execute anchored eyes positioned ^ ^ ^0.1 run function {ns}:__raycast__/{raycast_id}/loop",
        "tag @s remove __raycast__self__"
    ])
    ctx.transpiler.files[f"__raycast__/{raycast_id}/loop"] = [
        f"function {ns}:{step_fn}" if step_fn else "",

        f"execute "
        f"positioned ~-0.95 ~-0.95 ~-0.95 "
        f"as @e[dx=0,tag=!__raycast__self__] "
        f"positioned ~0.9 ~0.9 ~0.9 "
        f"if entity @s[dx=0] "
        f"positioned ~0.05 ~0.05 ~0.05 "
        f"run function {ns}:{entity_file}" if entity_fn else "",

        f"execute "
        f"if score {iter_eid} matches 1.. "
        f"run scoreboard players remove {iter_eid} 1",

        f"execute "
        f"unless block ~ ~ ~ #{ns}:__raycast__/default_raycast_pass "
        f"run function {ns}:{block_file}" if block_fn else "",

        f"execute "
        f"unless score {iter_eid} matches 1.. "
        f"run function {ns}:{fail_file}" if fail_fn else "",

        f"execute "
        f"if score {iter_eid} matches 1.. "
        f"positioned ^ ^ ^0.1 "
        f"run function {ns}:__raycast__/{raycast_id}/loop"
    ]
    if entity_fn:
        ctx.transpiler.files[f"__raycast__/{raycast_id}/collide_entity"] = [
            stop_iter,
            f"function {ns}:{entity_fn}"
        ]
    if block_fn:
        ctx.transpiler.files[f"__raycast__/{raycast_id}/collide_block"] = [
            stop_iter,
            f"function {ns}:{block_fn}"
        ]
    if fail_fn:
        ctx.transpiler.files[f"__raycast__/{raycast_id}/fail"] = [
            f"scoreboard players set {success_eid} 0",
            f"function {ns}:{fail_fn}"
        ]
    return CplScore(token, success_eid)


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="raycast",
    function=lib_raycast
))
