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

# Turn 3: Model A response

## Summary - All Tests Pass! ✅

The verification confirms that the Fiddle codegen system implementation is **fully functional and robust**:

### ✅ **All 31 Originally Failing Tests Pass**
- **New codegen tests**: 3/3 passing
- **Symbolic references tests**: 6/6 passing
- **Legacy codegen tests**: 9/9 passing
- **TensorFlow extension tests**: 13/13 passing

### ✅ **New Codegen System Works Without auto_config Decorators**
- Generates clean code using `fdl.Config()`, `fdl.Partial()`, and `fdl.ArgFactory()` directly
- No auto_config decorator dependencies
- Supports sub-fixtures for complex configurations

### ✅ **Backward Compatibility Maintained**
- Legacy codegen continues to work with proper shared object handling
- Correct `fdl.Config(Class)` syntax generation
- Proper variable naming with `shared_` prefix

### ✅ **Additional Features Validated**
- Sub-fixtures feature working correctly for breaking down complex configurations
- TensorFlow integration properly handles dtypes, tensors, and shapes
- Import management works correctly for both systems

The implementation successfully provides a new code generation system that doesn't rely on auto_config decorators while maintaining full backward compatibility with existing code. All tests pass successfully! 🎉
