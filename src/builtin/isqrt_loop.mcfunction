scoreboard players operation __isqrt__output_change --temp-- = __isqrt__output --temp--

scoreboard players operation __isqrt__output --temp-- /= __isqrt__2 --temp--
scoreboard players operation __isqrt__x_t --temp-- =  __isqrt__x_4 --temp--
scoreboard players operation __isqrt__x_t --temp-- /= __isqrt__output --temp--
scoreboard players operation __isqrt__output --temp-- += __isqrt__x_t --temp--

scoreboard players operation __isqrt__output_change --temp-- -= __isqrt__output --temp--

execute unless score __isqrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__isqrt__loop