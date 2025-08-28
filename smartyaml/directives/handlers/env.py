"""
Environment variable directive handlers.

Implements !env, !env_int, !env_float, !env_bool, and !secret directives
for accessing and type-converting environment variables.
"""

from typing import Any

from ...errors import require_list_length, require_type
from ..base import DirectiveContext, EnvironmentDirectiveHandler


class EnvHandler(EnvironmentDirectiveHandler):
    """Handler for !env directive - get string environment variable."""

    @property
    def directive_name(self) -> str:
        return "env"

    def handle(self, value: Any, context: DirectiveContext) -> str:
        """
        Handle !env directive: get environment variable as string.

        Args:
            value: List [var_name, default] or [var_name] (automatically validated)
            context: Processing context

        Returns:
            Environment variable value or default
        """
        var_name = value[0]
        default = value[1] if len(value) > 1 else None

        return self.get_env_value(var_name, default, context)


class EnvIntHandler(EnvironmentDirectiveHandler):
    """Handler for !env_int directive - get integer environment variable."""

    @property
    def directive_name(self) -> str:
        return "env_int"

    def handle(self, value: Any, context: DirectiveContext) -> int:
        """
        Handle !env_int directive: get environment variable as integer.

        Args:
            value: List [var_name, default] or [var_name]
            context: Processing context

        Returns:
            Environment variable value converted to integer
        """
        error_builder = self.get_error_builder(context)

        require_type(value, list, "!env_int directive", error_builder)
        require_list_length(
            value,
            min_length=1,
            max_length=2,
            field_name="!env_int directive",
            context_builder=error_builder,
        )

        var_name = value[0]
        default = value[1] if len(value) > 1 else 0

        require_type(var_name, str, "!env_int variable name", error_builder)

        env_value = self.get_env_value(var_name, str(default), context)
        return self.convert_to_type(env_value, int, var_name, context)


class EnvFloatHandler(EnvironmentDirectiveHandler):
    """Handler for !env_float directive - get float environment variable."""

    @property
    def directive_name(self) -> str:
        return "env_float"

    def handle(self, value: Any, context: DirectiveContext) -> float:
        """
        Handle !env_float directive: get environment variable as float.

        Args:
            value: List [var_name, default] or [var_name]
            context: Processing context

        Returns:
            Environment variable value converted to float
        """
        error_builder = self.get_error_builder(context)

        require_type(value, list, "!env_float directive", error_builder)
        require_list_length(
            value,
            min_length=1,
            max_length=2,
            field_name="!env_float directive",
            context_builder=error_builder,
        )

        var_name = value[0]
        default = value[1] if len(value) > 1 else 0.0

        require_type(var_name, str, "!env_float variable name", error_builder)

        env_value = self.get_env_value(var_name, str(default), context)
        return self.convert_to_type(env_value, float, var_name, context)


class EnvBoolHandler(EnvironmentDirectiveHandler):
    """Handler for !env_bool directive - get boolean environment variable."""

    @property
    def directive_name(self) -> str:
        return "env_bool"

    def handle(self, value: Any, context: DirectiveContext) -> bool:
        """
        Handle !env_bool directive: get environment variable as boolean.

        Args:
            value: List [var_name, default] or [var_name]
            context: Processing context

        Returns:
            Environment variable value converted to boolean
        """
        error_builder = self.get_error_builder(context)

        require_type(value, list, "!env_bool directive", error_builder)
        require_list_length(
            value,
            min_length=1,
            max_length=2,
            field_name="!env_bool directive",
            context_builder=error_builder,
        )

        var_name = value[0]
        default = value[1] if len(value) > 1 else False

        require_type(var_name, str, "!env_bool variable name", error_builder)

        env_value = self.get_env_value(var_name, str(default).lower(), context)
        return self.convert_to_type(env_value, bool, var_name, context)


class SecretHandler(EnvironmentDirectiveHandler):
    """Handler for !secret directive - get secret environment variable."""

    @property
    def directive_name(self) -> str:
        return "secret"

    def handle(self, value: Any, context: DirectiveContext) -> str:
        """
        Handle !secret directive: get secret environment variable.

        Similar to !env but with additional security considerations.

        Args:
            value: List [var_name, default] or [var_name]
            context: Processing context

        Returns:
            Secret environment variable value
        """
        error_builder = self.get_error_builder(context)

        require_type(value, list, "!secret directive", error_builder)
        require_list_length(
            value,
            min_length=1,
            max_length=2,
            field_name="!secret directive",
            context_builder=error_builder,
        )

        var_name = value[0]
        default = value[1] if len(value) > 1 else None

        require_type(var_name, str, "!secret variable name", error_builder)

        # Use centralized security checking for secrets
        from ...utils.security import create_security_checker

        security_checker = create_security_checker(self.config, context.file_path)
        security_checker.check_env_var_access(var_name, is_secret=True)

        return self.get_env_value(var_name, default, context)
