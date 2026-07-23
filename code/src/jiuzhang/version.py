"""SDK 版本号定义。

版本号遵循 PEP 440，对应 Git tag 形式：

* ``0.1.0a0``  ↔  ``v0.1.0-alpha.0``
* ``0.1.0rc1`` ↔  ``v0.1.0-rc.1``
* ``0.1.0``    ↔  ``v0.1.0``
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__: str = "0.1.0a30"
