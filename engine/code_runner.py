def run_python(code: str):
    # restricted builtins
    safe_globals = {"__builtins__": {}}
    safe_locals = {}

    # expose safe libraries
    import math, json
    safe_globals.update({"math": math, "json": json})

    try:
        import pandas as pd
        import numpy as np
        safe_globals.update({"pd": pd, "np": np})
    except:
        # pandas might not be available
        pass

    # execute code safely
    exec(code, safe_globals, safe_locals)

    # retrieve expected variable
    return safe_locals.get("ANSWER")
