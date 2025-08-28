# coding=utf-8
# Copyright 2022 The Fiddle-Config Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Changes callables to symbol references for non-auto_config codegen.

N.B. Please see codegen/auto_config for the auto_config version!!
"""

from typing import Callable

from fiddle import daglish
from fiddle._src import config as config_lib
from fiddle._src.codegen.auto_config import code_ir
from fiddle._src.codegen.auto_config import make_symbolic_references as ac_make_symbolic_references

is_plain_symbol_or_enum_value = (
    ac_make_symbolic_references.is_plain_symbol_or_enum_value
)
noop_history_comments = ac_make_symbolic_references.noop_history_comments


def import_symbols(task: code_ir.CodegenTask) -> None:
  """Pass that just adds imports for symbols.

  It can be useful to run this pass early, so that other naming passes don't
  generate names which conflict with imports.

  Args:
    task: Codegen task.
  """
  # Track if we've found any Buildables that need fdl import
  has_buildables = False

  for value, _ in daglish.iterate(task.top_level_call.all_fixture_functions()):
    if isinstance(value, config_lib.Buildable):
      has_buildables = True
      task.import_manager.add(config_lib.get_callable(value))
      task.import_manager.add(type(value))

      # Import the tags too.
      for arg_tags in value.__argument_tags__.values():
        for tag in arg_tags:
          task.import_manager.add(tag)
    elif is_plain_symbol_or_enum_value(value):
      # Only import actual symbols that have modules (functions, classes, enums)
      # Skip code IR objects, basic types, and containers
      if not isinstance(value, (code_ir.Name, code_ir.FixtureFunction,
                                 code_ir.VariableReference, code_ir.VariableDeclaration,
                                 code_ir.SymbolReference, code_ir.CodegenNode,
                                 list, tuple, dict, str, int, float, bool,
                                 type(None))):
        task.import_manager.add(value)

  # Import fdl only if we have Buildables
  if has_buildables:
    task.import_manager.add_by_name("fiddle._src.config")


def replace_callables_and_configs_with_symbols(
    task: code_ir.CodegenTask,
    *,
    format_history: Callable[
        ..., code_ir.HistoryComments
    ] = noop_history_comments,
) -> None:
  """Replaces callables and Buildables with symbolic versions.

  Args:
    task: Codegen task.
    format_history: Function used to format history for a buildable. Set to
      get_history_comments.format_history_for_buildable (or a functools.partial
      variant) to populate histories.
  """

  def traverse(value, state: daglish.State):
    if isinstance(value, config_lib.Buildable):
      # For the new codegen style, we want fdl.Config(...) or fdl.Partial(...)
      # The symbol should be the type of Buildable (Config or Partial)
      symbol = task.import_manager.add(type(value))
      # The first positional argument should be the callable
      buildable_type = task.import_manager.add(config_lib.get_callable(value))
      all_tags = value.__argument_tags__
      value = state.map_children(value)
      for arg, arg_tags in all_tags.items():
        tag_expr = [task.import_manager.add(tag) for tag in arg_tags]
        if arg not in value.__arguments__:
          raise ValueError(
              f"Tagged field '{arg}' of {value!r} is not found in its"
              f" arguments: {value.__arguments__}. This is likely because the"
              " tagged field doesn't yet have a value. Consider assigning a"
              " value to the field first or removing field tags from your"
              " config, for example using `fdl.clear_tags`."
          )
        value.__arguments__[arg] = code_ir.WithTagsCall(
            tag_symbol_expressions=tag_expr,
            item_to_tag=value.__arguments__[arg],
        )
      return code_ir.SymbolOrFixtureCall(
          symbol_expression=symbol,
          positional_arg_expressions=[code_ir.SymbolReference(buildable_type)],
          arg_expressions=config_lib.ordered_arguments(value),
          history_comments=format_history(value),
      )
    elif isinstance(value, code_ir.CodegenNode):
      # Code IR objects should not be converted to SymbolReferences
      # They should just map their children
      return state.map_children(value)
    elif isinstance(value, code_ir.Name):
      # Name objects are not CodegenNode but should not be converted to SymbolReferences
      return value
    elif is_plain_symbol_or_enum_value(value):
      # Container types should just map their children
      if isinstance(value, (list, dict, tuple)):
        return state.map_children(value)
      # Only convert actual callable/class symbols to SymbolReferences
      # Skip basic Python types
      if isinstance(value, (str, int, float, bool, type(None))):
        return value
      # Import and return a symbol reference for actual symbols (functions, classes, enums)
      return code_ir.SymbolReference(value)
    else:
      return state.map_children(value)

  for fn in task.top_level_call.all_fixture_functions():
    fn.replace_with(daglish.MemoizedTraversal.run(traverse, fn))
