
import js from "@eslint/js";
import pluginVue from 'eslint-plugin-vue';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from "eslint-config-prettier";

import vueESLintParser from 'vue-eslint-parser';

export default [
    js.configs.recommended,
    ...pluginVue.configs['flat/recommended'],
    ...tseslint.configs.recommended,
    eslintConfigPrettier,
    {
        "languageOptions": {
            "globals": {
                "Blob": false,
                "console": false,
                "define": false,
                "document": false,
                "fetch": false,
                "File": false,
                "FocusEvent": false,
                "FormData": false,
                "history": false,
                "HTMLButtonElement": false,
                "HTMLElement": false,
                "HTMLInputElement": false,
                "location": false,
                "Promise": false,
                "requestAnimationFrame": false,
                "require": false,
                "setTimeout": false,
                "URL": false,
                "URLSearchParams": false,
                "window": false
            },
            "parser": vueESLintParser,
            "parserOptions": {
                "ecmaVersion": 11,
                "sourceType": "module",
                "requireConfigFile": false,
                "parser": {
                    "ts": "@typescript-eslint/parser"
                }
            },
        },
        "rules": {
            "@typescript-eslint/no-unused-vars": [
                "error", { 
                    "argsIgnorePattern": "^_", 
                    "varsIgnorePattern": "^_",
                    "caughtErrorsIgnorePattern": "^_",
                }
            ],
            "semi": ["error", "always"],
        },
    },
];