import Theme from "vitepress/theme";
import "./styles/common.css";
import "./styles/vars.css";
import SvgImage from "./components/SvgImage.vue";
import TryOut from "./components/TryOut.vue";

if (typeof document !== "undefined") {
    setInterval(() => {
        document.querySelectorAll(".language-js>span.lang").forEach(i => i.innerText = "radon");
    }, 100);
}

export default {
    ...Theme,
    enhanceApp({ app }) {
        app.component("SvgImage", SvgImage);
        app.component("TryOut", TryOut);
    }
};
