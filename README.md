# `top-level-unit-tester`
A minimalist python script that constructs a unittest class from unit tests provided in a json file. It is designed to run top-level functions in all python modules at the root.

## Setup
It requires the `numpy` library. This repo was aimed originally to use only standard libraries (hence why I used `json` instead of `pyaml`), but I need to test with `numpy` right now so this is a hot patch to at least make it work with it.

This behavior may change in the future if I found a workaround. For the time being, I recomment using a virtual environment.

## Usage
Write your `tests.json` file and place it at the root. Then, execute the command
```sh
python -m unittest
```

## Format of Test Cases
Add a file named `tests.json` to the root and drop in any number of python files at the root as well. If your python file is called `prog.py` then you can write test cases as follows:
```json
{
  "prog": {
    "func": {
      "tests": [
        {
          "input": {
            "param": 42
          },
          "output": 8
        }
      ]
    }
  }
}
```

This tests that a function called `func` inside module `prog.py` returns `8` with a parameter called `param` whose argument is `42`. In other words
```py
# inside prog.py
assert func(42) == 8
```

### Custom Types
The tester provides a dictionary parser to allow types that are not native to Python.

#### Tuples
Suppose you want to pass a tuple inside a list to a parameter called `x` you can do so like this:
```json
"x": [{"tuple": [[4], "a", false, null]}]
```
Which is parsed into
```py
x=[((4,), "a", False, None)]
```
Unfortunately, you cannot nest in the opposite order (i.e. `([],)`) since the process of converting to tuples is recursive to make writing test cases easier.

#### `numpy` Array
If your function uses numpy either as an input parameter or outputs one as well, you can create them like this
```json
"x": {"ndarray": [[1,2,3],[4,5,6],[7,8,9]]}
```
Which is parsed into
```py
x=np.array([[1,2,3],[4,5,6],[7,8,9]])
```

### Non-deterministic functions
If your function is non-deterministic and has a clear set of correct answers you can also test with this framework. Consider a function `ndFunc(param)` that receives an int and returns at random some prime less than it. You can do the following
```json
{
  "prog": {
    "ndFunc": {
      "tests": [
        {
          "input": {
            "param": 20
          },
          "any of": [2, 3, 5, 7, 11, 13, 17]
        }
      ]
    }
  }
}
```
This is equivalent to
```py
assert ndFunc(20) in [2, 3, 5, 7, 11, 13, 17]
```
Be mindful that if you use both `output` and `any of` by mistake in the same test case `output` will take precendence.
