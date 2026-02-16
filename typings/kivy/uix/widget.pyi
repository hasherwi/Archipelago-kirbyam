""" FillType_* is not a real kivy type - just something to fill unknown typing. """

from typing import Any, Optional, Protocol

from ..graphics.texture import FillType_Drawable, FillType_Vec

class FillType_BindCallback(Protocol):
    def __call__(self, *args: Any) -> None: ...


class FillType_Canvas:
    def add(self, drawable: FillType_Drawable) -> None: ...

    def clear(self) -> None: ...

    def __enter__(self) -> None: ...

    def __exit__(self, *args: Any) -> None: ...


class Widget:
    canvas: FillType_Canvas
    width: int
    pos: FillType_Vec

    def bind(self,
             *,
             pos: FillType_BindCallback | None = ...,
             size: FillType_BindCallback | None = ...) -> None: ...

    def refresh(self) -> None: ...
