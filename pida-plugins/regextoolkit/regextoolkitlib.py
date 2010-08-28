#!usr/bin/python

#       regextoolkit.py
#       
#       Copyright 2009 ahmed youssef <xmonader@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.





import re

flags=dict(
        MULTILINE=re.MULTILINE,
        DOTALL=re.DOTALL,
        VERBOSE=re.VERBOSE,
        LOCALE=re.L,
        UNICODE=re.UNICODE,
        IGNORECASE=re.IGNORECASE,
        )

#def get_flags(**kw):
#    assert map(flags.has_key, kw.keys())
#    myflags=0
#    for k in kw.keys():
#        myflags |= flags[k]
#    return myflags

##sames as get_flags(**d)
def flags_from_dict(d=flags):
    assert all(k in flags for k in d)
    return sum(flags[k] for k in d)


match=re.match
capture_groups=lambda m: m.groups() if m else None
capture_named_groups=lambda m: m.groupdict() if m else None
all_matches=lambda reg, input: list(re.finditer(reg, input))
#print get_flags(MULTILINE=True, VERBOSE=True)

def test():
    pat=r'(?P<first>\w+)\s?(?P<digit>\d+)\s?(?P<last>\w+)'
    inp="Hello 99 World"
    m=match(pat, inp)
    if m:
      print capture_groups(m)
      print capture_named_groups(m)

if __name__=="__main__":
    test()
