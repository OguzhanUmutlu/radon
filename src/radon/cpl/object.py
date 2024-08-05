import json
from typing import List, Dict

from ._base import CompileTimeValue
from .float import CplFloat
from .int import CplInt
from .nbtobject import CplObjectNBT
from .string import CplString
from ..tokenizer import Token
from ..utils import CplDefObject


class CplObject(CompileTimeValue):
    def __init__(self, token=None, value=None, class_name=None):
        # type: (Token | None, Dict[str, CompileTimeValue] | None, str | None) -> None
        if value is None:
            value = dict()
        self.unique_type: CplDefObject
        super().__init__(token)
        self.value = value
        t = dict()
        for k, v in self.value.items():
            t[k] = v.unique_type
        self.unique_type = CplDefObject(t, class_name)

    def get_py_value(self):
        d = dict()
        for k, v in self.value.items():
            vl = v.get_py_value()
            if vl is None:
                return None
            d[k] = vl
        return d

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            return None
        py_val = self.get_py_value()
        if py_val is not None:
            ctx.file.append(f"data modify {nbt_loc} set value {json.dumps(py_val)}")
        else:
            init = []
            keys = []

            for k in self.value:
                v = self.value[k]
                v_py_val = v.get_py_value()
                if v_py_val is not None:
                    init.append(json.dumps(k) + ":" + json.dumps(v_py_val))
                else:
                    init.append(
                        json.dumps(k) + ":" + v.unique_type.get_sample_value()
                    )
                    keys.append(k)
            ctx.file.append(
                f"data modify {nbt_loc} set value {'{'}{','.join(init)}{'}'}"
            )

            for k in self.value:
                v = self.value[k]
                if k in keys:
                    v.cache(ctx, nbt_loc=f"{nbt_loc}.{k}", force="nbt")
        return CplObjectNBT(self.token, nbt_loc, self.unique_type)

    def _get_index(self, ctx, index: CompileTimeValue):
        if isinstance(index, CplInt) or isinstance(index, CplFloat) or isinstance(index, CplString):
            return self.value[str(index.value)]
        return self.cache(ctx).get_index(ctx, index)

    def _add(self, ctx, cpl):
        if isinstance(cpl, CplObject):
            if cpl.unique_type.class_name != self.unique_type.class_name:
                return None
            d = dict(self.value)
            d.update(cpl.value)
            return CplObject(self.token, d, self.unique_type.class_name)
        if not isinstance(cpl, CplObjectNBT):
            return None
        return self.cache(ctx)._add(ctx, cpl)

    def tellraw_object(self, ctx):
        py_v = self.get_py_value()
        if py_v is None:
            return self.cache(ctx).tellraw_object(ctx)
        return {"text": json.dumps(py_v)}
