# File: d (Python 2.4)

global notify, reentry, sReentry, oldExcepthook, wantStackDumpLog, wantStackDumpUpload, dumpOnExceptionInit
from pandac.PandaModules import getConfigShowbase
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.showbase.PythonUtil import fastRepr
from exceptions import Exception
import sys
import types
import traceback
notify = directNotify.newCategory('ExceptionVarDump')
config = getConfigShowbase()
reentry = 0

def _varDump__init__(self, *args, **kArgs):
    global reentry
    if reentry > 0:
        return None
    
    reentry += 1
    f = 1
    self._savedExcString = None
    self._savedStackFrames = []
    while True:
        
        try:
            frame = sys._getframe(f)
        except ValueError:
            e = None
            break
            continue

        f += 1
        self._savedStackFrames.append(frame)
    self._moved__init__(*args, **args)
    reentry -= 1

sReentry = 0

def _varDump__print(exc):
    global sReentry
    if sReentry > 0:
        return None
    
    sReentry += 1
    if not exc._savedExcString:
        s = ''
        foundRun = False
        for frame in reversed(exc._savedStackFrames):
            filename = frame.f_code.co_filename
            codename = frame.f_code.co_name
            if not foundRun and codename != 'run':
                continue
            
            foundRun = True
            s += '\nlocals for %s:%s\n' % (filename, codename)
            locals = frame.f_locals
            for var in locals:
                obj = locals[var]
                rep = fastRepr(obj)
                s += '::%s = %s\n' % (var, rep)
            
        
        exc._savedExcString = s
        exc._savedStackFrames = None
    
    notify.info(exc._savedExcString)
    sReentry -= 1

oldExcepthook = None
wantStackDumpLog = False
wantStackDumpUpload = False
variableDumpReasons = []
dumpOnExceptionInit = False

class _AttrNotFound:
    pass


def _excepthookDumpVars(eType, eValue, tb):
    origTb = tb
    excStrs = traceback.format_exception(eType, eValue, origTb)
    s = 'printing traceback in case variable repr crashes the process...\n'
    for excStr in excStrs:
        s += excStr
    
    notify.info(s)
    s = 'DUMPING STACK FRAME VARIABLES'
    foundRun = True
    while tb is not None:
        frame = tb.tb_frame
        code = frame.f_code
        codeNames = set(code.co_names)
        if not foundRun:
            if code.co_name == 'run':
                foundRun = True
            else:
                tb = tb.tb_next
        
        s += '\n  File "%s", line %s, in %s' % (code.co_filename, frame.f_lineno, code.co_name)
        stateStack = Stack()
        name2obj = { }
        for (name, obj) in frame.f_builtins.items():
            if name in codeNames:
                name2obj[name] = obj
                continue
        
        for (name, obj) in frame.f_globals.items():
            if name in codeNames:
                name2obj[name] = obj
                continue
        
        for (name, obj) in frame.f_locals.items():
            if name in codeNames:
                name2obj[name] = obj
                continue
        
        names = name2obj.keys()
        names.sort()
        names.reverse()
        traversedIds = set()
        for name in names:
            stateStack.push([
                name,
                name2obj[name],
                traversedIds])
        
        while len(stateStack) > 0:
            (name, obj, traversedIds) = stateStack.pop()
            r = fastRepr(obj, maxLen = 10)
            if type(r) is types.StringType:
                r = r.replace('\n', '\\n')
            
            s += '\n    %s = %s' % (name, r)
            if id(obj) not in traversedIds:
                attrName2obj = { }
                for attrName in codeNames:
                    attr = getattr(obj, attrName, _AttrNotFound)
                    if attr is not _AttrNotFound:
                        
                        try:
                            className = attr.__class__.__name__
                        except:
                            pass

                        if className == 'method-wrapper':
                            continue
                        
                        attrName2obj[attrName] = attr
                        continue
                
                if len(attrName2obj):
                    attrNames = attrName2obj.keys()
                    attrNames.sort()
                    attrNames.reverse()
                    ids = set(traversedIds)
                    ids.add(id(obj))
                    for attrName in attrNames:
                        obj = attrName2obj[attrName]
                        stateStack.push([
                            '%s.%s' % (name, attrName),
                            obj,
                            ids])
                    
                
            len(attrName2obj)
        tb = tb.tb_next
    if foundRun:
        s += '\n'
        if wantStackDumpLog:
            notify.info(s)
        
        if wantStackDumpUpload:
            excStrs = traceback.format_exception(eType, eValue, origTb)
            for excStr in excStrs:
                s += excStr
            
            timeMgr = None
            
            try:
                timeMgr = base.cr.timeManager
            except:
                
                try:
                    timeMgr = simbase.air.timeManager


            if timeMgr:
                timeMgr.setStackDump(s)
            
        
    
    oldExcepthook(eType, eValue, origTb)


def install(log, upload):
    global wantStackDumpLog, wantStackDumpUpload, dumpOnExceptionInit, oldExcepthook
    wantStackDumpLog = log
    wantStackDumpUpload = upload
    dumpOnExceptionInit = config.GetBool('variable-dump-on-exception-init', 0)
    if dumpOnExceptionInit:
        if not hasattr(Exception, '_moved__init__'):
            Exception._moved__init__ = Exception.__init__
            Exception.__init__ = _varDump__init__
        
    elif sys.excepthook is not _excepthookDumpVars:
        oldExcepthook = sys.excepthook
        sys.excepthook = _excepthookDumpVars
    

