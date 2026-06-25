_debug_mode: bool = False

def enable():
    """
    Method to enable the debug mode. 
    If enabled, more detailed informations will be shown 
    """
    global _debug_mode
    _debug_mode = True

def disable():
    """
    Method to disable the debug mode. 
    """
    global _debug_mode
    _debug_mode = False

def is_active() -> bool:
    return _debug_mode

def log(message: str) -> None:
    """
    Print message only when debug mode is active.
    """
    if _debug_mode:
        print(f"  [i] {message}")