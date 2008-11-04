/*
 *   moopython/moopython-utils.h
 *
 *   Copyright (C) 2004-2008 by Yevgen Muntyan <muntyan@tamu.edu>
 *
 *   This file is part of medit.  medit is free software; you can
 *   redistribute it and/or modify it under the terms of the
 *   GNU Lesser General Public License as published by the
 *   Free Software Foundation; either version 2.1 of the License,
 *   or (at your option) any later version.
 *
 *   You should have received a copy of the GNU Lesser General Public
 *   License along with medit.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MOO_PYTHON_UTILS_H
#define MOO_PYTHON_UTILS_H

#include <Python.h>
#include <glib-object.h>

G_BEGIN_DECLS

#define MOO_TYPE_PY_OBJECT (_moo_py_object_get_type())

PyObject    *_moo_py_object_ref             (PyObject       *obj);
void         _moo_py_object_unref           (PyObject       *obj);
GType        _moo_py_object_get_type        (void) G_GNUC_CONST;

PyObject    *_moo_strv_to_pyobject          (char          **strv);

/* result may not be freed */
int          _moo_pyobject_to_strv          (PyObject       *obj,
                                             char         ***dest);
int          _moo_pyobject_to_strv_no_null  (PyObject       *obj,
                                             char         ***dest);

PyObject    *_moo_object_slist_to_pyobject  (GSList         *list);
PyObject    *_moo_string_slist_to_pyobject  (GSList         *list);
PyObject    *_moo_boxed_slist_to_pyobject   (GSList         *list,
                                             GType           type);

PyObject    *_moo_gvalue_to_pyobject        (const GValue   *val);
void         _moo_pyobject_to_gvalue        (PyObject       *object,
                                             GValue         *value);

char        *_moo_py_err_string             (void);
void         _moo_py_init_print_funcs       (void);


#define return_Obj(obj) return Py_INCREF (obj), obj
#define return_Self     return_Obj (self)
#define return_None     return_Obj (Py_None)
/* avoid strict aliasing warnings */
#define return_True     return PyBool_FromLong (TRUE)
#define return_False    return PyBool_FromLong (FALSE)
#define return_Bool(v)  return PyBool_FromLong ((v) && TRUE)

#define return_Int(v)   return PyInt_FromLong (v)

#define return_AttrError(msg)       return PyErr_SetString (PyExc_AttributeError, msg), NULL
#define return_AttrErrorInt(msg)    return PyErr_SetString (PyExc_AttributeError, msg), -1
#define return_TypeError(msg)       return PyErr_SetString (PyExc_TypeError, msg), NULL
#define return_TypeErrorInt(msg)    return PyErr_SetString (PyExc_TypeError, msg), -1
#define return_RuntimeError(msg)    return PyErr_SetString (PyExc_RuntimeError, msg), NULL
#define return_RuntimeErrorInt(msg) return PyErr_SetString (PyExc_RuntimeError, msg), -1
#define return_ValueError(msg)      return PyErr_SetString (PyExc_ValueError, msg), NULL
#define return_ValueErrorInt(msg)   return PyErr_SetString (PyExc_ValueError, msg), -1


#if PY_MINOR_VERSION < 4
#define Py_InitializeEx(arg) Py_Initialize()

#define Py_IncRef _moo_Py_IncRef
#define Py_DecRef _moo_Py_DecRef
inline static void
Py_IncRef (PyObject *obj)
{
    Py_XINCREF (obj);
}

inline static void
Py_DecRef (PyObject *obj)
{
    Py_XDECREF (obj);
}
#endif


G_END_DECLS

#endif /* MOO_PYTHON_UTILS_H */
