import os

IS_RENDER = os.getenv("RENDER", "").lower() == "true"

if IS_RENDER:
    from .render import *
else:
    from .local import *
