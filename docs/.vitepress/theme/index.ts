import Theme from "vitepress/theme";
import "./styles/common.css";
import "./styles/vars.css";
import SvgImage from "./components/SvgImage.vue";
import TryOut from "./components/TryOut.vue";

export default {
    ...Theme,
    enhanceApp({ app }) {
        app.component("SvgImage", SvgImage);
        app.component("TryOut", TryOut);
    }
};
