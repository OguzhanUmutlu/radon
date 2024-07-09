# Input value is an integer stored in __sqrt__x --temp--

# float x_4 = x / 4;
# float output = x_4;
# iter: output = output / 2 + x_2 / output;

# ITERATION
# Target: output = (output / 2) + x_4 / (output / 2)
# output /= 2
# x_t = x_4
# x_t /= output
# output += x_t
# if output_change != 0: continue

# x_2 = x
# x_2 /= 2
scoreboard players operation __isqrt__x_4 --temp-- = __isqrt__x --temp--
scoreboard players operation __isqrt__x_4 --temp-- /= __isqrt__4 --temp--
scoreboard players operation __isqrt__output --temp-- = __isqrt__x_4 --temp--

function $PACK_NAME$:__lib__/__isqrt__loop

