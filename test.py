import sys
import json
import unittest
import importlib.util
from typing import Any
from collections.abc import Callable


class TupleDecoder:
    @staticmethod
    def __tuple_rec(l: list):
        return tuple(e if type(e) != list else TupleDecoder.__tuple_rec(e) for e in l)

    @staticmethod
    def tuplify(d: dict[str, Any]):
        if len(d) == 1 and "tuple" in d:
            l = d.get("tuple", [])
            if type(l) == list:
                return TupleDecoder.__tuple_rec(l)
            else:
                return d
        else:
            return d


def load_module(name: str, pckg: str) -> Callable | type | None:
    spec = importlib.util.find_spec(name)
    if spec is not None:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return getattr(module, pckg)
    else:
        return None


def funcFactory(key: str, func: Callable, params: dict, expected: str):
    def anon(self: unittest.TestCase):
        received = func(**params)
        msg = [f"{key} failed.", f"received {received}", f"expected {expected}"]
        msg = "\n".join(msg)
        self.assertEqual(received, expected, msg)

    return anon


def testFactory(name: str, filepath: str, module: str):
    methods = {}

    with open(filepath, encoding="utf-8") as f:
        mod_units = json.load(f, object_hook=TupleDecoder.tuplify)

    assert type(mod_units) == dict
    assert module in mod_units
    units = mod_units[module]
    assert type(units) == dict

    for ukey, unit in units.items():
        assert type(unit) == dict
        tests = unit["tests"]
        assert type(tests) == list
        func = load_module(module, ukey)
        for i, test in enumerate(tests):
            assert type(test) == dict
            test_in = test["input"]
            test_out = test["output"]
            methods[f"test_{ukey}_{i}"] = funcFactory(ukey, func, test_in, test_out)

    dyn_class = type(
        name,
        (unittest.TestCase,),
        methods,
    )

    return dyn_class

TestHomework = testFactory("TestHomework", "tests.json", "hw1")
TestHomework = testFactory("TestHomework", "tests.json", "hw2")

if __name__ == "__main__":
    unittest.main()
