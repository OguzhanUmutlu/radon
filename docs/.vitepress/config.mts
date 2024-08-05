import { defineConfig } from "vitepress";

const ogDescription = "Next Generation Datapack Development";
const ogImage = "https://oguzhanumutlu.github.io/assets/icon-round.png";
const ogTitle = "Radon";
const ogUrl = "https://oguzhanumutlu.github.io";

const discordLink = "https://discord.gg/xYjXnDp6h3";

export default defineConfig({
    title: `Radon`,
    description: "Next Generation Datapack Development",
    ignoreDeadLinks: true,

    base: "/radon/",

    head: [
        ["link", { rel: "icon", type: "image/png", href: "./assets/icon-round.png" }],
        ["meta", { property: "og:type", content: "website" }],
        ["meta", { property: "og:title", content: ogTitle }],
        ["meta", { property: "og:image", content: ogImage }],
        ["meta", { property: "og:url", content: ogUrl }],
        ["meta", { property: "og:description", content: ogDescription }],
        ["meta", { name: "theme-color", content: "#717aff" }]
    ],

    locales: {
        root: { label: "English" }
    },

    themeConfig: {
        logo: "./assets/icon-round.png",
        editLink: {
            pattern: "https://github.com/OguzhanUmutlu/radon/edit/main/docs/:path",
            text: "Suggest changes to this page"
        },
        socialLinks: [
            { icon: "discord", link: discordLink },
            { icon: "github", link: "https://github.com/OguzhanUmutlu/radon" }
        ],
        search: {
            provider: "local",
            options: {}
        },
        footer: {
            message: `Released under the MIT License.`,
            copyright: "Copyright © 2023-present OguzhanUmutlu & Radon Contributors"
        },
        nav: [
            { text: "Guide", link: "/guide/", activeMatch: "/guide/" },
            { text: "Try Out", link: "/tryout", activeMatch: "/tryout" },
            { text: "Changelog", link: "https://github.com/OguzhanUmutlu/radon/blob/main/CHANGELOG.md" }
        ],
        sidebar: {
            "/guide/": [
                {
                    text: "Guide",
                    items: [
                        {
                            text: "Getting Started",
                            link: "/guide/"
                        },
                        {
                            text: "Config",
                            link: "/guide/config/"
                        },
                        {
                            text: "Comments",
                            link: "/guide/comments"
                        },
                        {
                            text: "Command Features",
                            link: "/guide/command-features"
                        },
                        {
                            text: "Variables",
                            link: "/guide/variables"
                        },
                        {
                            text: "Functions",
                            link: "/guide/functions"
                        },
                        {
                            text: "Conditionals",
                            link: "/guide/conditionals"
                        },
                        {
                            text: "Loops",
                            link: "/guide/loops"
                        },
                        {
                            text: "Classes",
                            link: "/guide/classes"
                        },
                        {
                            text: "Enums",
                            link: "/guide/enums"
                        },
                        {
                            text: "Importing",
                            link: "/guide/importing"
                        },
                        {
                            text: "Built-in Features",
                            link: "/guide/built-in-features"
                        },
                        {
                            text: "Python API",
                            link: "/guide/python_api"
                        }
                    ]
                }
            ]
        }
    }
});