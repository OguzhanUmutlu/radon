def show_err(text, code, start, end):
    lines = code.split("\n")

    line_start = code[:start].count("\n")
    line_end = code[:end].count("\n")
    col_start = start - (code.rfind("\n", 0, start) + 1)
    col_end = end - (code.rfind("\n", 0, end) + 1)

    if line_start == line_end:
        lines[line_start] = (
            lines[line_start][:col_start]
            + "\033[31m\033[4m"
            + lines[line_start][col_start:col_end]
            + "\033[0m"
            + lines[line_start][col_end:]
        )
    else:
        lines[line_start] = (
            lines[line_start][:col_start]
            + "\033[31m\033[4m"
            + lines[line_start][col_start:]
            + "\033[0m"
        )
        for i in range(line_start + 1, line_end):
            lines[i] = "\033[31m\033[4m" + lines[i] + "\033[0m"
        lines[line_end] = (
            "\033[31m\033[4m"
            + lines[line_end][:col_end]
            + "\033[0m"
            + lines[line_end][col_end:]
        )

    start_line_index = max(0, line_start - 2)
    end_line_index = min(len(lines) - 1, line_end + 2)

    printing = ""

    for i in range(start_line_index, end_line_index + 1):
        prefix = f"{i + 1} | "
        printing += prefix + lines[i] + "\n"

    printing += text

    return printing


def raise_syntax_error(text, token):
    raise_error("SyntaxError", text, token)


def raise_syntax_error_t(text, code, start, end):
    raise_error_t("SyntaxError", text, code, start, end)


def raise_error(error, text, token):
    print("Token: " + str(token))
    token.end += 1
    raise_error_t(error, text, token.code, token.start, token.end)


def raise_error_t(error, text, code, start, end):
    raise SyntaxError(show_err(f"\n\033[31m{error}: {text}\033[0m", code, start, end))


def show_warning(text, token):
    print("Token: " + str(token))
    print(
        show_err(
            f"\n\033[31mWarning: {text}\033[0m", token.code, token.start, token.end
        )
    )
