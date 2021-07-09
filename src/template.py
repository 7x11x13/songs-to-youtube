from string import Template
import os

def make_filename_safe(s):
    invalid_filename = "INVALID"
    replace_char = "_"
    if len(s) == 0:
        return invalid_filename
    
    safe_chars = " .-_"
    s = "".join((c if c.isalnum() or c in safe_chars else replace_char) for c in s).strip()
    
    if s[0] in '.-':
        s = replace_char + s[1:]
    if s[-1] == ".":
        s = s[:-1] + replace_char
        
    device_names = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", 
                    "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", 
                    "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
    
    if os.name == "nt":
        if s.split(".")[0] in device_names:
            return invalid_filename
    
    return s
    

class SettingTemplate(Template):
    # template placeholders are of the form
    # ~{key}
    # can be escaped by writing ~~{key}
    delimiter = "~"

    # placeholder must be surrounded by braces
    idpattern = None

    # key can be anything without braces
    braceidpattern = r"[^{}]*"

    def safe_substitute(self, /, **kws):
        mapping = kws
        # Helper function for .sub()
        def convert(mo):
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                for arg in named.split('|'):
                    if arg in mapping:
                        return str(mapping[arg])
                    elif len(arg) >= 2 and arg[0] == '"' and arg[-1] == '"':
                        # string literal
                        return arg[1:-1]
                    elif len(arg) >= 2 and arg[0] == '<' and arg[-1] == '>':
                        # make value filename-safe
                        arg = arg[1:-1]
                        if arg in mapping:
                            return make_filename_safe(str(mapping[arg]))
                return mo.group()
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                return mo.group()
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)