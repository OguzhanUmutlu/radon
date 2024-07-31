import json
import re

from ..cpl.int import CplInt
from ..cpl.string import CplString
from ..error import raise_syntax_error
from ..transpiler import add_lib, CustomCplObject
from ..utils import VariableDeclaration, CplDefFunction, STRING_TYPE, get_str_count, get_expr_id

funcArgs = [CplDefFunction([], None)]  # (() => void)


def first_join_init(tr, file_name):
    tr.dp_files["advancements/__events__/on_first_join.json"] = json.dumps({
        "criteria": {
            "requirement": {
                "trigger": "minecraft:tick"
            }
        },
        "rewards": {
            "function": f"{tr.pack_namespace}:{file_name}"
        }
    }, indent=2)


def join_init(tr, file_name):
    tr.files[file_name].insert(0, f"scoreboard players operation @s on_join = counter? on_join")
    tr.load_file.append(f"scoreboard objectives add on_join dummy")
    tr.tick_file = [
                       "scoreboard players add counter? on_join 1",
                       "scoreboard players add @a on_join 1",
                       f"execute as @a unless score @s on_join = counter? on_join run function {tr.pack_namespace}:{file_name}"
                   ] + tr.tick_file


def die_common(tr):
    tr.load_file.append(f"scoreboard objectives add on_die deathCount")
    tr.tick_file = [
                       "execute as @a[scores={on_die=1}] at @s run function " + f"{tr.pack_namespace}:__events__/die",
                       "execute as @e[type=player,scores={__die__=2..}] at @s run function namespace:__events__/respawn"
                   ] + tr.tick_file


def die_init(tr, file_name):
    tr.files[file_name].insert(0, f"scoreboard players set @s on_die 2")
    respawn_file_name = f"__events__/respawn"
    if respawn_file_name not in tr.files:
        tr.files[respawn_file_name] = [f"scoreboard players set @s on_die 0"]
    die_common(tr)


def respawn_init(tr, file_name):
    tr.files[file_name].insert(0, f"scoreboard players set @s on_die 0")
    die_file_name = f"__events__/die"
    if die_file_name not in tr.files:
        tr.files[die_file_name] = [f"scoreboard players set @s on_die 2"]
    die_common(tr)


def stick_init(tr, file_name, item):
    tr.load_file.append(f"scoreboard objectives add on_{item} used:{item}")
    tr.tick_file.insert(0,
                        "execute as @a[scores={on_" + item + "=1..}] at @s run function " + f"{tr.pack_namespace}:{file_name}")

    tr.files[file_name].insert(0, f"scoreboard players set @s on_{item} 0")


def listener_on(ctx, arguments, token):
    tr = ctx.transpiler
    if ctx.function or ctx.loop:
        raise_syntax_error("Player.on() can only be called in the main scope", token)
    tr.assert_args("Player.on", [
        STRING_TYPE, CplDefFunction([], None)
    ], arguments, token)
    arg0 = arguments[0]
    arg1 = arguments[1]
    if not isinstance(arg0, CplString) or not isinstance(arg1, CplString):
        raise_syntax_error("Expected a literal string as the first argument for Player.on()", token)
    event = arg0.value
    event = event.lower()
    obj_type = event

    if event == "rejoin":
        obj_type = "custom:leave_game"
    if event == "sneak":
        obj_type = "custom:sneak_time"
    if event == "sprint":
        obj_type = "custom:sprint_one_cm"
    # only a-z allowed, use regex
    event_str = str(get_str_count(event))
    file_name = (f"__events__/{event}"
                 if re.fullmatch(r"[a-z_]+", event)
                 else f"__events__/{event_str}")

    if file_name not in tr.files:

        tr.files[file_name] = []
        if event == "firstjoin":
            first_join_init(tr, file_name)
        elif event == "join":
            join_init(tr, file_name)
        elif event == "die":
            die_init(tr, file_name)
        elif event == "respawn":
            respawn_init(tr, file_name)
        elif event == "carrot_on_a_stick" or event == "warped_fungus_on_a_stick":
            stick_init(tr, file_name, event)
        else:
            tr.files[file_name].insert(0, f"scoreboard players set @s on_{event_str} 0")
            tr.load_file.append(f"scoreboard objectives add on_{event_str} {obj_type}")
            tr.tick_file.insert(0,
                                "execute as @a[scores={on_" + event_str + "=1..}] at @s run function " + tr.pack_namespace + ":" + file_name)

    arg1_fn = tr.get_fn(arg1.value, [], token)

    eid = get_expr_id()

    tr.files[file_name].append(
        f"execute if score __event__{event_str}_{eid} __temp__ matches 1..1 run function {tr.pack_namespace}:{arg1_fn.file_name}")

    ctx.file.append(f"scoreboard players set @s __event__{event_str}_{eid} __temp__ 1")

    return CplInt(token, 0)  # returns 0 as an int


add_lib(VariableDeclaration(
    name="Listener",
    type=CustomCplObject({
        "on": listener_on
    }),
    constant=True
))
