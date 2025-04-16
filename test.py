import os
import sys
import json
import numpy
import unittest
import importlib.util
from typing import Any
from types import ModuleType
from collections.abc import Callable


class DictDecoder:
    @staticmethod
    def __tuple_rec(l: list):
        return tuple(e if type(e) != list else DictDecoder.__tuple_rec(e) for e in l)

    @staticmethod
    def tuplify(d: dict[str, Any]):
        if len(d) == 1 and "tuple" in d:
            l = d.get("tuple", [])
            if type(l) == list:
                return DictDecoder.__tuple_rec(l)
            else:
                return d
        if len(d) == 1 and "set" in d:
            l = d.get("set", [])
            if type(l) == list:
                return set(l)
            else:
                return d
        elif len(d) == 1 and "ndarray" in d:
            l = d.get("ndarray", [])
            if type(l) == list:
                return numpy.array(l)
            else:
                return d
        else:
            return d


def load_module(name: str):
    spec = importlib.util.find_spec(name)
    if spec is not None:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    else:
        return None


def get_module_member(module: ModuleType | None, object: str) -> Callable | type | None:
    if module is not None:
        return getattr(module, object)
    else:
        return None


def errMsg():
    a = "\n1st -> received, 2nd -> expected\n"
    b = "function call:\n{}({})"
    return a + b


def testFactory(key: str, func: Callable, params: dict, expected: Any):
    def anon(self: unittest.TestCase):
        received = func(**params)
        msgpar = ",".join(f"{k}={e}" for k, e in params.items())
        msg = errMsg().format(key, msgpar)
        self.assertEqual(received, expected, msg)

    return anon


def fuzzyTestFactory(key: str, func: Callable, params: dict, expectedList: list[Any]):
    def anon(self: unittest.TestCase):
        received = func(**params)
        msgpar = ",".join(f"{k}={e}" for k, e in params.items())
        msg = f"{key}({msgpar}) failed."
        self.assertIn(received, expectedList, msg)

    return anon


def unitFactory(name: str, filepath: str, include: tuple[str] | None = None):
    methods = {}

    with open(filepath, encoding="utf-8") as f:
        mod_units = json.load(f, object_hook=DictDecoder.tuplify)

    assert type(mod_units) == dict

    for modKey, units in mod_units.items():
        assert type(units) == dict
        assert os.path.exists(f"{modKey}.py")

        if include is not None and modKey not in include:
            continue

        module = load_module(modKey)
        assert module is not None

        for unitKey, unit in units.items():
            assert type(unit) == dict
            tests = unit["tests"]
            assert type(tests) == list
            func = get_module_member(module, unitKey)
            assert func is not None

            for i, test in enumerate(tests):
                assert type(test) == dict
                test_in = test["input"]
                if "output" in test:
                    test_out = test["output"]
                    factory = testFactory
                elif "any of" in test:
                    test_out = test["any of"]
                    factory = fuzzyTestFactory
                else:
                    raise KeyError(
                        "each test case should have either `output` or `any of` fields"
                    )
                methods[f"test_{modKey}_{unitKey}_{i}"] = factory(
                    unitKey, func, test_in, test_out
                )

    dyn_class = type(
        name,
        (unittest.TestCase,),
        methods,
    )

    return dyn_class


TestFunctions = unitFactory("TestFunctions", "tests.json")

if __name__ == "__main__":
    unittest.main()
