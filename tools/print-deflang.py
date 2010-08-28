
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pida.services.language.deflang import DEFMAPPING


lexers = list(get_all_lexers())



def tryremoveall(entry, name, items):
    if name not in entry:
        return
    if isinstance(entry[name], basestring):
        print 'omg', entry['human'], name
        data = set([entry[name]])
    else:
        data = set(entry[name])
    data -= set(items)
    if data:
        entry[name] = sorted(data)
    else:
        del entry[name]

def cleanup(name, alias, glob, mime):
    if name not in DEFMAPPING:
        return
    clean_entry(DEFMAPPING[name], name, alias, glob, mime)


def clean_entry(entry, name, alias, glob, mime):
    tryremoveall(entry, 'glob', glob)
    tryremoveall(entry, 'mime', mime)
    tryremoveall(entry, 'alias', alias)
    if name == entry.get('human'):
        del entry['human']


for lexer in lexers:
    cleanup(*lexer)



def lexer_by_name_or_alias(name, alias):
    try: return get_lexer_by_name(name)
    except:
        for name in alias:
            try:
                return get_lexer_by_name(name)
            except:
                pass
    raise ValueError


for name, entry in DEFMAPPING.items():
    try:
        lexer = lexer_by_name_or_alias(name, entry['alias'])
        entry['module'] = lexer.__module__.split('.')[-1]
        clean_entry(entry, lexer.name, lexer.aliases, lexer.filenames, lexer.mimetypes)
    except:
        pass
    clean_entry(entry, name, (), (), (),)


#import yaml
#print yaml.dump(DEFMAPPING)
