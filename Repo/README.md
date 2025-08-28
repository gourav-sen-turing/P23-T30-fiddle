# Fiddle


Fiddle is a Python-first configuration library particularly well suited to ML
applications. Fiddle enables deep configurability of parameters in a program,
while allowing configuration to be expressed in readable and maintainable Python
code.

Additional details can be found in the [documentation].

[documentation]: https://fiddle.readthedocs.io


### Setup


Install Fiddle with pip:

```shell
pip install fiddle
```

Install Fiddle from source:

```shell
git clone https://github.com/google/fiddle
cd fiddle
python -m setup install
```

Import Fiddle:

```python
import fiddle as fdl
```

# Turn 1: Model A response

## Analysis and Understanding

Based on my investigation of the repository and failing tests, here's my understanding of the requirements:

### Current State:
1. **Files already exist** that were mentioned as needing to be created:
- `fiddle/_src/codegen/legacy_codegen.py` - Already exists
- `fiddle/_src/codegen/new_codegen.py` - Already exists
- `fiddle/_src/codegen/newcg_symbolic_references.py` - Already exists

2. **Public API file** `fiddle/codegen/codegen.py` imports from `legacy_codegen`

3. **The main issue is a bug** in `legacy_codegen.py` (line 273) where the callable and buildable type are swapped in the generated code

### Key Issues to Fix:

1. **Legacy Codegen Bug (line 273)**:
- Current: `f"{relname}({buildable_subclass_str})"`
- Should be: `f"{buildable_subclass_str}({relname})"`
- This is causing `test_util.Foo(fdl.Config)` instead of `fdl.Config(test_util.Foo)`

2. **New Codegen Symbolic References Issue**:
- The `import_symbols` function in `newcg_symbolic_references.py` has wrong error handling
- It should skip FixtureFunction objects, not raise an error
- The condition at line 54 is too strict

3. **IR to CST Handling**:
- The `ir_to_cst.py` already handles `None` auto_config_fn properly (lines 171-176)
- It conditionally adds the decorator only when auto_config_fn exists

### Failing Test Categories:

1. **Legacy codegen tests** - Failing due to the swapped arguments bug
2. **New codegen tests** - Failing due to the import_symbols error
3. **Extension tests (tf_test.py)** - May be failing due to import issues after renaming

### Proposed Approach:

1. **Fix the legacy_codegen.py bug** by swapping the arguments at line 273
2. **Fix newcg_symbolic_references.py** to properly handle the iteration without raising errors for lists
3. **Ensure all imports are updated** if there was a renaming needed (though it seems files were already created)

The PR description mentioned renaming `codegen.py` to `legacy_codegen.py`, but this seems to have already been done. The main issues are bugs in the existing implementations rather than missing files.
