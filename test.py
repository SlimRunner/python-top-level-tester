import io
import os
import sys
import json
import numpy
import unittest
import importlib.util
from typing import Any
from types import ModuleType
from unittest.mock import patch
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


def testFactory(
    key: str,
    func: Callable,
    params: dict,
    ret_expect: Any,
    retval_set: list[Any] | None = None,
    stdin: str | list[str] | None = None,
    stdout_expect: str | None = None,
    stderr_expect: str | None = None,
    mapper: Callable[[Any, str, str], tuple[Any, str, str]] | None = None,
):
    if type(stdin) == str:
        stdin = stdin.split("\n")
    elif stdin is None:
        stdin = []

    def anon(self: unittest.TestCase):
        with patch("builtins.input", side_effect=stdin):
            stdout_buff = io.StringIO()
            stderr_buff = io.StringIO()
            sys.stdout = stdout_buff
            sys.stderr = stderr_buff
            try:
                ret_recv = func(**params)
            except Exception as e:
                raise e
            finally:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__

            stdout_recv = stdout_buff.getvalue()
            stderr_recv = stderr_buff.getvalue()
            if mapper is not None:
                ret_recv, stdout_recv, stderr_recv = mapper(
                    ret_recv, stdout_recv, stderr_recv
                )

        msgpar = ",".join(f"{k}={e}" for k, e in params.items())
        msg = errMsg().format(key, msgpar)
        if retval_set is None:
            self.assertEqual(ret_recv, ret_expect, msg)
        else:
            self.assertIn(ret_recv, retval_set, msg)

        if stdout_expect is not None:
            self.assertEqual(stdout_recv, stdout_expect, msg)
        if stderr_expect is not None:
            self.assertEqual(stderr_recv, stderr_expect, msg)

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
                test_in = test.get("input", None)
                test_out = test.get("output", None)
                test_any = test.get("any of", None)
                test_stdin = test.get("stdin", None)
                test_stdout = test.get("stdout", None)
                test_stderr = test.get("stderr", None)
                test_mapper = test.get("mapper", None)
                if test_mapper is not None:
                    test_mapper = get_module_member(module, test_mapper)

                methods[f"test_{modKey}_{unitKey}_{i}"] = testFactory(
                    unitKey,
                    func,
                    test_in,
                    test_out,
                    test_any,
                    test_stdin,
                    test_stdout,
                    test_stderr,
                    test_mapper,
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
