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

# Turn 1: Model B response

## Summary of Understanding

Based on my analysis of the repository and failing tests, here's what I understand about the requirements:

### Current State:
1. There's an existing codegen system in `fiddle/_src/codegen/legacy_codegen.py` that uses auto_config decorators
2. New files have been created:
- `new_codegen.py` - New API for code generation without auto_config decorators
- `newcg_symbolic_references.py` - Handles symbolic references for the new system
3. The new system is partially implemented but has bugs causing test failures

### Key Issues Found:

1. **In `newcg_symbolic_references.py`:**
- The `import_symbols` function has a bug where it's incorrectly raising an error for plain symbols
- It should import plain symbols like the original does, not raise an error
- It's missing the import for `fdl` (Fiddle) itself

2. **In `new_codegen.py`:**
- The `new_codegen` function is not passing `sub_fixtures` parameter correctly (it always passes None)

3. **Missing support for handling cases without auto_config decorator:**
- The `ir_to_cst.py` needs to handle the case where `task.auto_config_fn` is None

### Requirements:
1. The original `codegen.py` file doesn't exist - it's already `legacy_codegen.py`
2. The new code generation system should produce code using `fdl.Config()`, `fdl.Partial()`, and `fdl.ArgFactory()` directly instead of auto_config decorators
3. The system should maintain backward compatibility with existing code

## Proposed Approach:

1. **Fix `newcg_symbolic_references.py`:**
- Fix the `import_symbols` function to properly handle all types of values
- Fix the `replace_callables_and_configs_with_symbols` function to correctly swap the symbol expression and positional arguments for the new style

2. **Fix `new_codegen.py`:**
- Pass the `sub_fixtures` parameter correctly to the codegen object

3. **Update `ir_to_cst.py`:**
- Ensure it handles the case when `auto_config_fn` is None (no decorator)

4. **Update import references:**
- The public API in `fiddle/codegen/codegen.py` already imports from `legacy_codegen`
- Need to ensure the import_manager is updated if needed

Let me now proceed with implementing these fixes to make the tests pass.

# Turn 3: Model B response

## Summary of Verification Results

### ✅ **All 31 originally failing tests are now passing**

### ✅ **New Codegen System Works Correctly:**
- Generates code WITHOUT auto_config decorators
- Uses `fdl.Config()`, `fdl.Partial()`, and `fdl.ArgFactory()` directly
- Properly handles sub_fixtures
- Correctly processes nested configurations
- Handles ArgFactory instances appropriately

### ✅ **Legacy Codegen System Maintains Backward Compatibility:**
- Still generates `build_config()` functions
- Correctly orders arguments (`fdl.Config(Class)` not `Class(fdl.Config)`)
- Properly handles shared objects with correct variable prefixes
- Works with all existing test cases

### ✅ **TensorFlow Extension Works Correctly:**
- DType handling is correct
- Tensor conversion generates proper `tensorflow.constant()` calls
- Printing and serialization work as expected
- All 13 TensorFlow extension tests pass

### Key Implementation Changes Verified:
1. **legacy_codegen.py**: Fixed argument order swap bug
2. **newcg_symbolic_references.py**: Fixed import handling and traversal logic
3. **new_codegen.py**: Fixed sub_fixtures parameter passing
4. **tf.py**: Fixed module names and tensor conversion
5. **printing.py**: Fixed display order
6. **formatting_utilities.py**: Removed incorrect integer handling

The implementation successfully provides a new code generation system that doesn't rely on auto_config decorators while maintaining full backward compatibility with the existing system. All originally failing tests now pass, confirming the robustness of the solution.


# Note:
- venv folder is kept empty as it was taking 700-900mb after compressed into a zip
