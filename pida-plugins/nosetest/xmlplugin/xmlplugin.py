"""This is a very basic example of a plugin that controls all test
output. In this case, it formats the output as ugly unstyled html.

Upgrading this plugin into one that uses a template and css to produce
nice-looking, easily-modifiable html output is left as an exercise for
the reader who would like to see his or her name in the nose AUTHORS file.
"""
import traceback
from xml.sax.saxutils import escape, quoteattr
from nose.plugins import Plugin


class XmlOutput(Plugin):
    """Output test results as ugly, unstyled html.
    """
    
    name = 'xml-output'
    score = 2 # run late
    
    def __init__(self):
        super(XmlOutput, self).__init__()
        self.html = [ '<?xml version="1.0" encoding="utf-8"?>',
                      '<suite>' ]
    
    def addSuccess(self, test):
        self.html.append('<result status="ok" />')
        
    def addError(self, test, err):
        err = self.formatErr(err)
        self.html.append('<result status="error">')
        self.html.append('%s</result>' % escape(err))
            
    def addFailure(self, test, err):
        err = self.formatErr(err)
        self.html.append('<result status="fail">')
        self.html.append('%s</result>' % escape(err))

    def finalize(self, result):
        self.html.append(
        '<summery ran="%d" failures="%d" errors="%d" successful="%d" />' 
                         %(result.testsRun, len(result.failures),
                           len(result.errors),
                           result.wasSuccessful() and 1 or 0))
        self.html.append('</suite>')
        # print >> sys.stderr, self.html
        for l in self.html:
            self.stream.writeln(l)

    def formatErr(self, err):
        exctype, value, tb = err
        return ''.join(traceback.format_exception(exctype, value, tb))
    
    def setOutputStream(self, stream):
        # grab for own use
        self.stream = stream        
        # return dummy stream
        class dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
        d = dummy()
        return d

    def startContext(self, ctx):
        self.html.append('<context>')
        try:
            n = ctx.__name__
        except AttributeError:
            n = str(ctx)
        self.html.append('<name>%s</name>' %escape(n))
        try:
            path = ctx.__file__.replace('.pyc', '.py')
            self.html.append('<path>%s</path>' %escape(path))
        except AttributeError:
            pass

    def stopContext(self, ctx):
        self.html.append('</context>')
    
    def startTest(self, test):
        self.html.extend([ '<test><description>',
                           escape(test.shortDescription() or str(test)),
                           '</description>' ])
        
    def stopTest(self, test):
        self.html.append('</test>')
