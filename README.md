# `top-level-unit-tester`
A minimalist python script that constructs a unittest class from unit tests provided in a json file. It is designed to run top-level functions in all python modules at the root or any of its packages.

## Setup
It requires the `numpy` library. This repo was aimed originally to use only standard libraries (hence why it uses `json` instead of `pyaml`). Until a better solution is found to allow custom types without external libraries, it will remain like this. It is recommended to use a virtual environment.

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

This test asserts that a function called `func` inside module `prog.py` returns `8` with a parameter called `param` whose argument is `42`. In other words
```py
# inside prog.py
assert func(42) == 8
```
Note that `prog` could be a fully qualified Python package. For example, `myPackage.util.foo` for `./myPackage/util/foo`.

### Custom Types
The tester provides a dictionary parser to allow types that are not native to Python.

#### Tuples
The following
```json
"x": [{"tuple": [[4], "a", false, null]}]
```
is parsed into
```py
x=[((4,), "a", False, None)]
```
**These work recursively**. Since the hook for dictionaries in the `json` parser bottom up (not top down), it is not possible to to nest lists the other way (i.e. `([],)`). This limitation is a trade off to allow writing complex nested tuples without too much boiler plate.

#### Sets
The following
```json
"x": [{"set": ["a", false, null]}]
```
is parsed into
```py
x={"a", False, None}
```
**These are not recursive**. It only converts into a set the top level list.

#### Float
The following
```json
"x": {"float": "inf"}
```
is parsed into
```py
x=float("inf")
```

#### `numpy` Array
If your function uses numpy either as an input parameter or outputs one as well, you can create them like this
```json
"x": {"ndarray": [[1,2,3],[4,5,6],[7,8,9]]}
```
Which is parsed into
```py
x=np.array([[1,2,3],[4,5,6],[7,8,9]])
```
This may or may not be recursive. The tester simply passes the top level item to `np.array` as shown.

### Test Other Forms of Output
The tester allows to inject standard input as well as to capture standard output and standard error. To do this simply add appropriately called `stdin`, `stdout`, and or `stderr` to the respective test. All of these **must** be strings. Any of them can be omitted. For the last two no tests are run if they are missing.

Similarly you may also leave out the `output` key. However, this will not waive the test. The tester defaults to test if the return value is `null`. Keep this in mind if you are only testing the standard io.

### Kinds of Tests
By using the `kind` property in the respective test you can define a custom kind of assertion for `unittest`. If omitted `assertEqual` is used to test the return value of the function. Check the full list of assertions at [Python standard library docs](https://docs.python.org/3/library/unittest.html#assert-methods). Only the ones with binary arity work (the ones with two parameters).

If you include `kind` property the only valid format is as follows
```json
"kind": ["kind_for_return", "kind_for_stdout", "kind_for_stdin"]
```

It must have 3 items, but they do not have to exist or be valid. In case they are not valid asserts then `assertEqual` is used. Therefore if you wish to only define the one for `stdout` you can do the following
```json
"kind": ["", "assertIn", null]
```
Notice can use anything for the ones you don't want to define. The tester will automatically put those to the default without crashing.

### Mappers
If for whatever reason none of the assertions fit your needs you may define a helper function in your module to test and pass it to the property `mapper`. Such function has to have the following signature
```py
def mapper(ret: Any, stdout: str, stderr: str) -> (Any, str, str):
    return ret, stdout, stderr
```
In there you can mutate whatever your function generated so that it matches the type of return value you defined as the expected value. This is valuable when a function you cannot control prints to standard output a lot of text, but you only care about one that you can distill out of it.

## Full Format Spec
```jsonc
{
  /* can be a fully qualified module name */
  "module1": {
    "func1": {
      "tests": [
        {
          /* may be omitted or set to {} */
          "input": {
            "param1": {},
            "param2": {}
            /* ... */
          },

          /* may be omitted */
          "kind": ["", "assert...", null],

          /* may be omitted. Value may be any valid json type */
          "output": 0,

          /* may be omitted. Can be a normal string instead of a list */
          "stdin": [
            "multi line",
            "text to be consumed"
          ],

          /* may be omitted. Must be a string or list of strings */
          "stdout": "",

          /* may be omitted. Must be a string or list of strings */
          "stderr": "",

          /* may be omitted. Read section for expected signature */
          "mapper": "mapper",

          /* may be omitted. Must be string and unique among this test set.*/
          /* Can use "{}" for numbering */
          "tag": "tag"
        }
      ]
    },
    "func2": { /* ... */ },
    /* ... */
  },
  "module2": { /* ... */ },
  /* ... */
}
```
