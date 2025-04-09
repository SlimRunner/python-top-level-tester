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
assert(func(42) == 8)
```

It also supports tuples. For example, suppose you want to pass a tuple inside a list to a parameter called `x` you can do so like this:
```json
"x": [{"tuple": [[4], "a", false, null]}]
```
Which is parsed into
```py
x=[((4,), "a", False, None)]
```
Unfortunately, you cannot nest in the opposite order. The lists would just turn into tuples.

However, if you wish to modify this behavior you can do so at the static method `tuplify` in the `TupleDecoder` class. On the other hand if you want to define them completely different, say as strings, you can also do that. You'd have to modify the code at line
```py
mod_units = json.load(f, object_hook=TupleDecoder.tuplify)
```
There are tons of resources to write this so I will not put that here, but [the documentation are a good starting point](https://docs.python.org/3/library/json.html).

# Usage
To run, execute the command
```sh
python -m unittest
```
