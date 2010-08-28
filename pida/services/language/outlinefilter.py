from pida.utils.languages import LANG_OUTLINER_TYPES

FILTERMAP = {
    LANG_OUTLINER_TYPES.IMPORT: {
        "name": "import",
        "alias": "include",
        "display": "Imports",
        "icon": "source-import",
        "default": True 
    },
    LANG_OUTLINER_TYPES.BUILTIN: {
        "name": "builtin",
        "alias": "",
        "display": "Builtins",
        "icon": "source-module",
        "default": True
    },
    LANG_OUTLINER_TYPES.ATTRIBUTE: {
        "name": "attribute",
        "alias": "",
        "display": "Attributes",
        "icon": "source-attribute",
        "default": True
    },
    LANG_OUTLINER_TYPES.METHOD: {
        "name": "method",
        "alias": "",
        "display": "Methods",
        "icon": "source-method",
        "default": True
    },
    LANG_OUTLINER_TYPES.PROPERTY: {
        "name": "property",
        "alias": "",
        "display": "Properties",
        "icon": "source-property",
        "default": True
    },
    LANG_OUTLINER_TYPES.FUNCTION: {
        "name": "function",
        "alias": "",
        "display": "Functions",
        "icon": "source-function",
        "default": True
    },
    LANG_OUTLINER_TYPES.SUPERMETHOD: {
        "name": "import",
        "alias": "include",
        "display": "Super methods",
        "icon": "source-extramethod",
        "default": True 
    },
    LANG_OUTLINER_TYPES.SUPERPROPERTY: {
        "name": "import",
        "alias": "include",
        "display": "Super properties",
        "icon": "source-extramethod",
        "default": True 
    },
} 
