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
    def parse(d: dict[str, Any]):
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
        if len(d) == 1 and "ndarray" in d:
            l = d.get("ndarray", [])
            if type(l) == list:
                return numpy.array(l)
            else:
                return d
        if len(d) == 1 and "float" in d:
            l = d.get("float", [])
            if type(l) == str:
                return float(l)
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
    assert_kinds: tuple[str | None, str | None, str | None] | None = None,
    stdin: str | list[str] | None = None,
    stdout_expect: str | list[str] | None = None,
    stderr_expect: str | list[str] | None = None,
    mapper: Callable[[Any, str, str], tuple[Any, str, str]] | None = None,
):
    if type(stdin) == str:
        stdin = stdin.split("\n")
    elif stdin is None:
        stdin = []

    if stdout_expect is not None and isinstance(stdout_expect, list):
        stdout_expect = "\n".join(stdout_expect)

    if stderr_expect is not None and isinstance(stderr_expect, list):
        stderr_expect = "\n".join(stderr_expect)

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

        if assert_kinds is None or len(assert_kinds) != 3:
            ret_assert = "assertEqual"
            stdout_assert = "assertEqual"
            stderr_assert = "assertEqual"
        else:
            # yes that was on purpose
            asserts = []
            for asskind in assert_kinds:
                if type(asskind) == str and hasattr(self, asskind):
                    asserts.append(asskind)
                else:
                    asserts.append("assertEqual")
            ret_assert, stdout_assert, stderr_assert = asserts

        msgpar = ",".join(f"{k}={e}" for k, e in params.items())
        msg = errMsg().format(key, msgpar)
        getattr(self, ret_assert)(ret_recv, ret_expect, msg)

        if stdout_expect is not None:
            getattr(self, stdout_assert)(stdout_recv, stdout_expect, msg)
        if stderr_expect is not None:
            getattr(self, stderr_assert)(stderr_recv, stderr_expect, msg)

    return anon


def unitFactory(filepath: str, include: tuple[str] | None = None):
    with open(filepath, encoding="utf-8") as f:
        mod_units = json.load(f, object_hook=DictDecoder.parse)

    assert type(mod_units) == dict
    dyn_classes: dict[tuple[str, type]] = {}

    for modKey, units in mod_units.items():
        methods = {}
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
            tag_set = set()

            for i, test in enumerate(tests):
                assert type(test) == dict
                test_in = test.get("input", {})
                test_out = test.get("output", None)
                test_kind = test.get("kind", None)
                test_stdin = test.get("stdin", None)
                test_stdout = test.get("stdout", None)
                test_stderr = test.get("stderr", None)
                test_mapper = test.get("mapper", None)
                test_tag = test.get("tag", None)
                if test_tag is not None:
                    assert type(test_tag) == str
                    test_tag = f"test_{test_tag.format(i)}"
                    assert test_tag not in tag_set
                else:
                    test_tag = f"test_{unitKey}_{i}"
                tag_set.add(test_tag)
                if test_mapper is not None:
                    test_mapper = get_module_member(module, test_mapper)

                methods[test_tag] = testFactory(
                    unitKey,
                    func,
                    test_in,
                    test_out,
                    test_kind,
                    test_stdin,
                    test_stdout,
                    test_stderr,
                    test_mapper,
                )

        dyn_class = type(
            f"Test_{modKey}",
            (unittest.TestCase,),
            methods,
        )
        dyn_classes[f"Test_{modKey}"] = dyn_class

    return dyn_classes


globals().update(unitFactory("tests.json"))

if __name__ == "__main__":
    unittest.main()
