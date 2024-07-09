scoreboard players operation __fsqrt__output_change --temp-- = __fsqrt__output --temp--

scoreboard players operation __fsqrt__output --temp-- /= __fsqrt__2 --temp--
scoreboard players operation __fsqrt__x_t --temp-- =  __fsqrt__x_4 --temp--
scoreboard players operation __fsqrt__x_t --temp-- /= __fsqrt__output --temp--
scoreboard players operation __fsqrt__x_t --temp-- *= FLOAT_PREC --temp--
scoreboard players operation __fsqrt__output --temp-- += __fsqrt__x_t --temp--

scoreboard players operation __fsqrt__output_change --temp-- -= __fsqrt__output --temp--

execute unless score __fsqrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__fsqrt__loop