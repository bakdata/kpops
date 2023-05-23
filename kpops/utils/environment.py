import platform


class Environment(dict):
    def __init__(self, mapping=None, /, **kwargs) -> None:
        if platform.system() == "Windows":
            if mapping is not None:
                mapping = {
                    str(key).upper(): value for key, value in mapping.items()
                }
            else:
                mapping = {}
            if kwargs:
                mapping.update(
                    {str(key).upper(): value for key, value in kwargs.items()}
                )
        super().__init__(mapping)

