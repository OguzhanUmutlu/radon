# Try Out

<TryOut />

<script type="module">;

const namespace = () => document.getElementById("namespace");
const code = () => document.getElementById("code");
const filesDiv = () => document.querySelector(".files");
const versionDiv = () => document.getElementById("version");

async function waitLoad() {
    if (!versionDiv()) return await new Promise(resolve => setTimeout(() => waitLoad().then(resolve), 100));
}

async function main() {
    if (!window.pyodide) {
        console.log("Loading pyodide.");
        console.time("Loaded pyodide");
        window.pyodide = await loadPyodide();
        console.timeEnd("Loaded pyodide");
    }

    if (!pyodide.loadedPackages.radonmc) {
        console.log("Loading radon...");
        console.time("Loaded radon");
        if (!pyodide.loadedPackages.micropip) await pyodide.loadPackage("micropip");
        const pip = pyodide.pyimport("micropip");
        await pip.install("radonmc", { headers: { pragma: "no-cache", "cache-control": "no-cache" } });
        console.timeEnd("Loaded radon");
    }

    await waitLoad();

    const VERSION = pyodide.runPython(`from radon.utils import VERSION_RADON
VERSION_RADON`);
    versionDiv().innerText = "Radon v" + VERSION;

    namespace().addEventListener("input", updateCode);
    code().addEventListener("input", updateCode);
    code().addEventListener("keydown", e => {
        if (e.key === "Tab") {
            e.preventDefault();
            insertCode("    ");
        }
    });
}

function transpile(namespace, code) {
    return pyodide.runPython(`import json
from radon.transpiler import Transpiler
from radon.dp_ast import parse_str
from radon.utils import reset_expr_id

def main(namespace, code):
    try:
        reset_expr_id()
        transpiler = Transpiler()
        transpiler.pack_namespace = namespace
        (statement, macros) = parse_str(code)
        transpiler.transpile(statement, macros)

        for filename in transpiler.files:
            transpiler.files[filename] = "\\n".join(transpiler.files[filename])

        return json.dumps(transpiler.files)
    except SyntaxError as e:
        return str(e)

main`)(namespace, code);
}

function updateCode() {
    code().style.height = "auto";
    code().style.height = code.scrollHeight + "px";

    for (const child of [...filesDiv().children]) {
        filesDiv().removeChild(child);
    }

    if (!code().value.trim()) return;

    let transpiled = transpile(namespace().value || "namespace", code().value);

    if (transpiled[0] != "{") {
        transpiled = transpiled.split(/(\x1b\[31m)|(\x1b\[4m)|(\x1b\[0m)/).filter(i => i);
        const error = document.createElement("div");
        error.classList.add("error");
        let colored = false;
        let underline = false;
        for (const t of transpiled) {
            if (t === "\x1b[31m") {
                colored = true;
                continue;
            }
            if (t === "\x1b[4m") {
                underline = true;
                continue;
            }
            if (t === "\x1b[0m") {
                colored = false;
                underline = false;
                continue;
            }

            const span = document.createElement("span");
            span.innerText = t;

            if (colored) span.style.color = "red";
            if (underline) span.style.textDecoration = "underline";

            error.appendChild(span);
        }
        filesDiv().appendChild(error);
        return;
    }

    const files = JSON.parse(transpiled);

    for (const filename in files) {
        const text = files[filename];
        const file = document.createElement("div");
        file.classList.add("file");

        const name = document.createElement("div");
        name.classList.add("filename");
        name.innerText = filename + ".mcfunction";
        file.appendChild(name);

        const content = document.createElement("div");
        content.classList.add("file-content");
        content.innerText = text;
        file.appendChild(content);

        filesDiv().appendChild(file);
    }
}

function insertCode(textToInsert) {
    const cursorPosition = code.selectionStart;

    const textBefore = code.value.substring(0, cursorPosition);
    const textAfter = code.value.substring(cursorPosition, code.value.length);

    code.value = textBefore + textToInsert + textAfter;

    code.selectionStart = cursorPosition + textToInsert.length;
    code.selectionEnd = code.selectionStart;
}

if (typeof document != "undefined") {
    eval(`import("https://cdn.jsdelivr.net/pyodide/v0.26.1/full/pyodide.js")`).then(main);
}
</script>