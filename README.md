# Setup
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
          "output": "8"
        }
      ]
    }
  }
}
```

This tests that a function called `func` inside module `prog.py` returns `8` (the tester turns it into a string you can return a regular number) with a parameter called `param` whose argument is `42`. In other words
```py
# inside prog.py
assert(str(func(42)) == "8")
```

You can edit the behavior of turning things into strings at [test.py](./test.py) inside `funcFactory`. Also, you can define tuples like this
```json
{"tuple": [[4],3]}
```
Which is parsed into
```py
((4),3)
```
If you wish to modify this behavior you can do so at the static method `tuplify` in the `TupleDecoder` class. You can modify it to parse stings directly using python equivalent of eval. I wanted something safer so I used this but feel free to modify it to your convenience.

# Usage
To run execute the command
```sh
python -m unittest
```
