class PipelineStateNotInitializedException(Exception):
    def __init__(self, message="PipelineState was not initialized correctly"):
        super().__init__(message)


class ClassNotFoundError(Exception):
    """Similar to builtin ModuleNotFoundError; class doesn't exist inside module."""
