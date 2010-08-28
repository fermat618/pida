from pida.utils.languages import OUTLINER

FILTERMAP = {
    OUTLINER.IMPORT: {
        "name": "import",
        "alias": "include",
        "display": "Imports",
        "icon": "source-import",
        "default": True 
    },
    OUTLINER.BUILTIN: {
        "name": "builtin",
        "alias": "",
        "display": "Builtins",
        "icon": "source-module",
        "default": True
    },
    OUTLINER.ATTRIBUTE: {
        "name": "attribute",
        "alias": "",
        "display": "Attributes",
        "icon": "source-attribute",
        "default": True
    },
    OUTLINER.METHOD: {
        "name": "method",
        "alias": "",
        "display": "Methods",
        "icon": "source-method",
        "default": True
    },
    OUTLINER.PROPERTY: {
        "name": "property",
        "alias": "",
        "display": "Properties",
        "icon": "source-property",
        "default": True
    },
    OUTLINER.FUNCTION: {
        "name": "function",
        "alias": "",
        "display": "Functions",
        "icon": "source-function",
        "default": True
    },
    OUTLINER.SUPERMETHOD: {
        "name": "import",
        "alias": "include",
        "display": "Super methods",
        "icon": "source-extramethod",
        "default": True 
    },
    OUTLINER.SUPERPROPERTY: {
        "name": "import",
        "alias": "include",
        "display": "Super properties",
        "icon": "source-extramethod",
        "default": True 
    },
} 
