from typing import Any

message_location: str

class DeprecatedWarning(DeprecationWarning):
    function: Any
    deprecated_in: Any
    removed_in: Any
    details: Any
    def __init__(
        self, function: Any, deprecated_in: Any, removed_in: Any, details: str = ...
    ) -> None: ...

class UnsupportedWarning(DeprecatedWarning): ...

def deprecated(
    deprecated_in: Any | None = ...,
    removed_in: Any | None = ...,
    current_version: Any | None = ...,
    details: str = ...,
) -> Any: ...
def fail_if_not_removed(method): ...
