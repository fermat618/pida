/*
 *   mootype-macros.h
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

#ifndef MOO_TYPE_MACROS_H
#define MOO_TYPE_MACROS_H

#include <glib-object.h>

#if !GLIB_CHECK_VERSION(2,14,0)
inline static gboolean
_moo_once_init_enter (volatile gsize *value_location)
{
    return *value_location == 0;
}

inline static void
_moo_once_init_leave (volatile gsize *value_location,
                      gsize           initialization_value)
{
    *value_location = initialization_value;
}
#elif !GLIB_CHECK_VERSION(2,16,0)
inline static gboolean
_moo_once_init_enter (volatile gsize *value_location)
{
    return g_once_init_enter ((volatile gpointer*) value_location);
}

inline static void
_moo_once_init_leave (volatile gsize *value_location,
                      gsize           initialization_value)
{
    g_once_init_leave ((volatile gpointer*) value_location,
                       (gpointer) initialization_value);
}
#else
#define _moo_once_init_enter g_once_init_enter
#define _moo_once_init_leave g_once_init_leave
#endif

#if !GLIB_CHECK_VERSION(2,12,0)
#define _MOO_REGISTER_TYPE(TypeName,type_name,TYPE_PARENT,flags)                            \
    static const GTypeInfo type_info = {                                                    \
        sizeof (TypeName##Class),                                                           \
        (GBaseInitFunc) NULL,                                                               \
        (GBaseFinalizeFunc) NULL,                                                           \
        (GClassInitFunc) type_name##_class_intern_init,                                     \
        (GClassFinalizeFunc) NULL,                                                          \
        NULL,   /* class_data */                                                            \
        sizeof (TypeName),                                                                  \
        0,      /* n_preallocs */                                                           \
        (GInstanceInitFunc) type_name##_init,                                               \
        NULL    /* value_table */                                                           \
    };                                                                                      \
                                                                                            \
    g_define_type_id =                                                                      \
        g_type_register_static (TYPE_PARENT, #TypeName, &type_info, (GTypeFlags) flags);
#else
#define _MOO_REGISTER_TYPE(TypeName,type_name,TYPE_PARENT,flags)                            \
    g_define_type_id =                                                                      \
        g_type_register_static_simple (TYPE_PARENT,                                         \
                                       g_intern_static_string (#TypeName),                  \
                                       sizeof (TypeName##Class),                            \
                                       (GClassInitFunc) type_name##_class_intern_init,      \
                                       sizeof (TypeName),                                   \
                                       (GInstanceInitFunc) type_name##_init,                \
                                       (GTypeFlags) flags);
#endif


#define MOO_DEFINE_TYPE_STATIC_WITH_CODE(TypeName,type_name,TYPE_PARENT,code)               \
                                                                                            \
static GType    type_name##_get_type (void) G_GNUC_CONST;                                   \
static void     type_name##_init              (TypeName        *self);                      \
static void     type_name##_class_init        (TypeName##Class *klass);                     \
static gpointer type_name##_parent_class = NULL;                                            \
                                                                                            \
static void     type_name##_class_intern_init (gpointer klass)                              \
{                                                                                           \
    type_name##_parent_class = g_type_class_peek_parent (klass);                            \
    type_name##_class_init ((TypeName##Class*) klass);                                      \
}                                                                                           \
                                                                                            \
static GType                                                                                \
type_name##_get_type (void)                                                                 \
{                                                                                           \
    static volatile gsize g_define_type_id__volatile;                                       \
                                                                                            \
    if (_moo_once_init_enter (&g_define_type_id__volatile))                                 \
    {                                                                                       \
        GType g_define_type_id;                                                             \
        _MOO_REGISTER_TYPE(TypeName,type_name,TYPE_PARENT,0)                                \
        code                                                                                \
        _moo_once_init_leave (&g_define_type_id__volatile, g_define_type_id);               \
    }                                                                                       \
                                                                                            \
    return g_define_type_id__volatile;                                                      \
}

#define MOO_DEFINE_TYPE_STATIC(TypeName,type_name,TYPE_PARENT)                              \
    MOO_DEFINE_TYPE_STATIC_WITH_CODE (TypeName, type_name, TYPE_PARENT, {})


#define MOO_DEFINE_BOXED_TYPE__(TypeName,type_name,copy_func,free_func)                     \
{                                                                                           \
    static volatile gsize g_define_type_id__volatile;                                       \
                                                                                            \
    if (_moo_once_init_enter (&g_define_type_id__volatile))                                 \
    {                                                                                       \
        GType g_define_type_id =                                                            \
            g_boxed_type_register_static (#TypeName,                                        \
                                          (GBoxedCopyFunc) copy_func,                       \
                                          (GBoxedFreeFunc) free_func);                      \
        _moo_once_init_leave (&g_define_type_id__volatile, g_define_type_id);               \
    }                                                                                       \
                                                                                            \
    return g_define_type_id__volatile;                                                      \
}

#define MOO_DEFINE_BOXED_TYPE(TypeName,type_name,copy_func,free_func)                       \
GType type_name##_get_type (void)                                                           \
    MOO_DEFINE_BOXED_TYPE__(TypeName,type_name,copy_func,free_func)

#define MOO_DEFINE_BOXED_TYPE_C(TypeName,type_name) \
    MOO_DEFINE_BOXED_TYPE(TypeName,type_name,type_name##_copy,type_name##_free)

#define MOO_DEFINE_BOXED_TYPE_R(TypeName,type_name) \
    MOO_DEFINE_BOXED_TYPE(TypeName,type_name,type_name##_ref,type_name##_unref)

#define MOO_DEFINE_BOXED_TYPE_STATIC(TypeName,type_name,copy_func,free_func)                \
static GType type_name##_get_type (void) G_GNUC_CONST;                                      \
static GType type_name##_get_type (void)                                                    \
    MOO_DEFINE_BOXED_TYPE__(TypeName,type_name,copy_func,free_func)

#define MOO_DEFINE_BOXED_TYPE_STATIC_C(TypeName,type_name) \
    MOO_DEFINE_BOXED_TYPE_STATIC(TypeName,type_name,type_name##_copy,type_name##_free)

#define MOO_DEFINE_BOXED_TYPE_STATIC_R(TypeName,type_name) \
    MOO_DEFINE_BOXED_TYPE_STATIC(TypeName,type_name,type_name##_ref,type_name##_unref)


#define MOO_DEFINE_POINTER_TYPE(TypeName,type_name)                                         \
GType type_name##_get_type (void)                                                           \
{                                                                                           \
    static volatile gsize g_define_type_id__volatile;                                       \
                                                                                            \
    if (_moo_once_init_enter (&g_define_type_id__volatile))                                 \
    {                                                                                       \
        GType g_define_type_id = g_pointer_type_register_static (#TypeName);                \
        _moo_once_init_leave (&g_define_type_id__volatile, g_define_type_id);               \
    }                                                                                       \
                                                                                            \
    return g_define_type_id__volatile;                                                      \
}


#define MOO_DEFINE_QUARK__(QuarkName)                                                       \
{                                                                                           \
    static volatile gsize q_volatile;                                                       \
                                                                                            \
    if (_moo_once_init_enter (&q_volatile))                                                 \
    {                                                                                       \
        GQuark q = g_quark_from_static_string (#QuarkName);                                 \
        _moo_once_init_leave (&q_volatile, q);                                              \
    }                                                                                       \
                                                                                            \
    return q_volatile;                                                                      \
}

#define MOO_DEFINE_QUARK(QuarkName,quark_func)                                              \
GQuark quark_func (void)                                                                    \
    MOO_DEFINE_QUARK__(QuarkName)

#define MOO_DEFINE_QUARK_STATIC(QuarkName,quark_func)                                       \
static GQuark quark_func (void) G_GNUC_CONST;                                               \
static GQuark quark_func (void)                                                             \
    MOO_DEFINE_QUARK__(QuarkName)


#endif /* MOO_TYPE_MACROS_H */
