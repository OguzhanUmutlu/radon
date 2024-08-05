class RadonError(Exception):
    def __init__(self, err, text, code, start, end):
        super().__init__(err)
        self.err = err
        self.text = text
        self.code = code
        self.start = start
        self.end = end


def show_err(color, text, code, start, end):
    lines = code.split("\n")

    line_start = code[:start].count("\n")
    line_end = code[:end].count("\n")
    col_start = start - (code.rfind("\n", 0, start) + 1)
    col_end = end - (code.rfind("\n", 0, end) + 1)

    if line_start == line_end:
        ls = lines[line_start]
        lines[line_start] = (
                ls[:col_start]
                + "\033[" + color + "m\033[4m"
                + ls[col_start:col_end]
                + "\033[0m" + "\033[" + color + "m"
                + ls[col_end:]
        )
    else:
        ls = lines[line_start]
        lines[line_start] = (
                ls[:col_start]
                + "\033[" + color + "m\033[4m"
                + ls[col_start:]
                + "\033[0m"
        )
        for i in range(line_start + 1, line_end):
            lines[i] = "\033[" + color + "m\033[4m" + lines[i] + "\033[0m"
        lines[line_end] = (
                "\033[" + color + "m\033[4m"
                + lines[line_end][:col_end]
                + "\033[0m"
                + lines[line_end][col_end:]
        )

    line_inc = 0 if color == "33" else 2
    start_line_index = max(0, line_start - line_inc)
    end_line_index = min(len(lines) - 1, line_end + line_inc)

    printing = ""

    for i in range(start_line_index, end_line_index + 1):
        prefix = f"{i + 1} | "
        printing += prefix + lines[i] + ("\n" if color == "31" else "")

    printing += text

    return printing


def raise_syntax_error(text, token):
    raise_error("SyntaxError", text, token)


def raise_syntax_error_t(text, code, start, end):
    raise_error_t("SyntaxError", text, code, start, end)


def raise_error(error, text, token):
    # print("Token: " + str(token))
    token.end += 1
    raise_error_t(error, text, token.code, token.start, token.end)


def raise_error_t(error, text, code, start, end):
    raise RadonError(
        show_err("31", f"\n\033[31m" + (f"{error}: " if error else "") + f"{text}\033[0m", code, start, end),
        text, code, start, end)


def show_warning(text, token):
    # print("Token: " + str(token))
    print(
        show_err("33",
                 f"\n\033[33mWarning: {text}\033[0m", token.code, token.start, token.end
                 )
    )
