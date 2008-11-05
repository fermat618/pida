from argtypes import ArgType, matcher

class StrvArg(ArgType):
    def write_param(self, ptype, pname, pdflt, pnull, info):
        if pdflt:
            if pdflt != 'NULL': raise TypeError("Only NULL is supported as a default char** value")
            info.varlist.add('char', '**' + pname + ' = ' + pdflt)
        else:
            info.varlist.add('char', '**' + pname)
        info.arglist.append(pname)
        if pnull:
            info.add_parselist('O&', ['_moo_pyobject_to_strv', '&' + pname], [pname])
        else:
            info.add_parselist('O&', ['_moo_pyobject_to_strv_no_null', '&' + pname], [pname])
    def write_return(self, ptype, ownsreturn, info):
        if ownsreturn:
            # have to free result ...
            info.varlist.add('char', '**ret')
            info.varlist.add('PyObject', '*py_ret')
            info.codeafter.append('    py_ret = _moo_strv_to_pyobject (ret);\n' +
                                  '    g_strfreev (ret);\n' +
                                  '    return py_ret;')
        else:
            info.varlist.add('char', '**ret')
            info.codeafter.append('    return _moo_strv_to_pyobject (ret);')

class StringSListArg(ArgType):
    def write_return(self, ptype, ownsreturn, info):
        if ownsreturn:
            # have to free result ...
            info.varlist.add('GSList', '*ret')
            info.varlist.add('PyObject', '*py_ret')
            info.codeafter.append('    py_ret = _moo_string_slist_to_pyobject (ret);\n' +
                                  '    g_slist_foreach (ret, (GFunc) g_free, NULL);\n' +
                                  '    g_slist_free (ret);\n' +
                                  '    return py_ret;')
        else:
            info.varlist.add('GSList', '*ret')
            info.codeafter.append('    return _moo_string_slist_to_pyobject (ret);')

class ObjectSListArg(ArgType):
    def write_return(self, ptype, ownsreturn, info):
        if ownsreturn:
            # have to free result ...
            info.varlist.add('GSList', '*ret')
            info.varlist.add('PyObject', '*py_ret')
            info.codeafter.append('    py_ret = _moo_object_slist_to_pyobject (ret);\n' +
                                  '    g_slist_foreach (ret, (GFunc) g_object_unref, NULL);\n' +
                                  '    g_slist_free (ret);\n' +
                                  '    return py_ret;')
        else:
            info.varlist.add('GSList', '*ret')
            info.codeafter.append('    return _moo_object_slist_to_pyobject (ret);')

class NoRefObjectSListArg(ArgType):
    def write_return(self, ptype, ownsreturn, info):
        if ownsreturn:
            # have to free result ...
            info.varlist.add('GSList', '*ret')
            info.varlist.add('PyObject', '*py_ret')
            info.codeafter.append('    py_ret = _moo_object_slist_to_pyobject (ret);\n' +
                                  '    g_slist_free (ret);\n' +
                                  '    return py_ret;')
        else:
            info.varlist.add('GSList', '*ret')
            info.codeafter.append('    return _moo_object_slist_to_pyobject (ret);')

arg = StrvArg()
matcher.register('strv', arg)

arg = StringSListArg()
matcher.register('string-slist', arg)
arg = ObjectSListArg()
matcher.register('object-slist', arg)
arg = NoRefObjectSListArg()
matcher.register('no-ref-object-slist', arg)
