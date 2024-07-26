import{_ as _export_sfc,D as resolveComponent,c as createElementBlock,I as createVNode,j as createBaseVNode,a as createTextVNode,o as openBlock}from"./chunks/framework.DzjGgv20.js";const namespace=()=>document.getElementById("namespace"),code=()=>document.getElementById("code"),filesDiv=()=>document.querySelector(".files"),versionDiv=()=>document.getElementById("version");async function waitLoad(){if(!versionDiv())return await new Promise(e=>setTimeout(()=>waitLoad().then(e),100))}async function main(){window.pyodide||(console.log("Loading pyodide."),console.time("Loaded pyodide"),window.pyodide=await loadPyodide(),console.timeEnd("Loaded pyodide")),pyodide.loadedPackages.radonmc||(console.log("Loading radon..."),console.time("Loaded radon"),pyodide.loadedPackages.micropip||await pyodide.loadPackage("micropip"),await pyodide.pyimport("micropip").install("radonmc",{headers:{pragma:"no-cache","cache-control":"no-cache"}}),console.timeEnd("Loaded radon")),await waitLoad();const e=pyodide.runPython(`from radon.utils import VERSION_RADON
VERSION_RADON`);versionDiv().innerText="Radon v"+e,namespace().addEventListener("input",updateCode),code().addEventListener("input",updateCode),code().addEventListener("keydown",t=>{t.key==="Tab"&&(t.preventDefault(),insertCode("    "))})}function transpile(e,t){return pyodide.runPython(`import json
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

main`)(e,t)}function updateCode(){code().style.height="auto",code().style.height=code.scrollHeight+"px";for(const o of[...filesDiv().children])filesDiv().removeChild(o);if(!code().value.trim())return;let e=transpile(namespace().value||"namespace",code().value);if(e[0]!="{"){e=e.split(/(\x1b\[31m)|(\x1b\[4m)|(\x1b\[0m)/).filter(n=>n);const o=document.createElement("div");o.classList.add("error");let r=!1,i=!1;for(const n of e){if(n==="\x1B[31m"){r=!0;continue}if(n==="\x1B[4m"){i=!0;continue}if(n==="\x1B[0m"){r=!1,i=!1;continue}const a=document.createElement("span");a.innerText=n,r&&(a.style.color="red"),i&&(a.style.textDecoration="underline"),o.appendChild(a)}filesDiv().appendChild(o);return}const t=JSON.parse(e);for(const o in t){const r=t[o],i=document.createElement("div");i.classList.add("file");const n=document.createElement("div");n.classList.add("filename"),n.innerText=o+".mcfunction",i.appendChild(n);const a=document.createElement("div");a.classList.add("file-content"),a.innerText=r,i.appendChild(a),filesDiv().appendChild(i)}}function insertCode(e){const t=code.selectionStart,o=code.value.substring(0,t),r=code.value.substring(t,code.value.length);code.value=o+e+r,code.selectionStart=t+e.length,code.selectionEnd=code.selectionStart}typeof document<"u"&&eval('import("https://cdn.jsdelivr.net/pyodide/v0.26.1/full/pyodide.js")').then(main);const __pageData=JSON.parse('{"title":"Try Out","description":"","frontmatter":{},"headers":[],"relativePath":"tryout.md","filePath":"tryout.md"}'),_sfc_main={name:"tryout.md"},_hoisted_1=createBaseVNode("h1",{id:"try-out",tabindex:"-1"},[createTextVNode("Try Out "),createBaseVNode("a",{class:"header-anchor",href:"#try-out","aria-label":'Permalink to "Try Out"'},"​")],-1);function _sfc_render(e,t,o,r,i,n){const a=resolveComponent("TryOut");return openBlock(),createElementBlock("div",null,[_hoisted_1,createVNode(a)])}const tryout=_export_sfc(_sfc_main,[["render",_sfc_render]]);export{__pageData,tryout as default};
