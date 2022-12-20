import typer


def yellowify(string: str) -> str:
    return typer.style(string, fg=typer.colors.YELLOW)


def greenify(string: str) -> str:
    return typer.style(string, fg=typer.colors.GREEN)


def magentaify(string: str) -> str:
    return typer.style(string, fg=typer.colors.MAGENTA)
