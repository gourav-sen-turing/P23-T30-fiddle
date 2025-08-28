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

  # Keep track of whether we need fdl import
  needs_fdl = False

  # Iterate over each fixture function's content
  for fn in task.top_level_call.all_fixture_functions():
    for value, _ in daglish.iterate(fn):
      if isinstance(value, config_lib.Buildable):
        needs_fdl = True
        task.import_manager.add(config_lib.get_callable(value))
        task.import_manager.add(type(value))

        # Import the tags too.
        for arg_tags in value.__argument_tags__.values():
          for tag in arg_tags:
            task.import_manager.add(tag)
      # Skip basic types, code_ir objects, and strings
      elif (not isinstance(value, (config_lib.Buildable, str, int, float, bool, type(None)))
            and hasattr(value, '__module__')
            and value.__class__.__module__ not in ('fiddle._src.codegen.auto_config.code_ir', 'builtins')
            and is_plain_symbol_or_enum_value(value)):
        try:
          task.import_manager.add(value)
        except (AttributeError, TypeError):
          # Skip values that can't be imported
          pass

  # Only import fdl if we found Buildables
  if needs_fdl:
    task.import_manager.add_by_name("fiddle")


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
      symbol = task.import_manager.add(type(value))
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
    elif is_plain_symbol_or_enum_value(value):
      # Don't convert code_ir types, lists, dicts, or basic types to SymbolReferences
      # Only convert actual importable symbols
      if (isinstance(value, (str, int, float, bool, type(None), list, dict, tuple))
          or (hasattr(value, '__class__') and
              value.__class__.__module__ == 'fiddle._src.codegen.auto_config.code_ir')):
        return state.map_children(value)
      else:
        return code_ir.SymbolReference(value)
    else:
      return state.map_children(value)

  for fn in task.top_level_call.all_fixture_functions():
    fn.replace_with(daglish.MemoizedTraversal.run(traverse, fn))
