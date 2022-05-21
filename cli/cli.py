import getopt, textwrap, sys

class UnknownCommand(Exception):
    def __init__(self, command, argv):
        self.Command = command
        self.Argv = argv
        
    def __str__(self):
        return f"Uknown command: {self.Command}\n" + \
            f"    command line: {self.Argv}"

class EmptyCommandLine(Exception):
    pass
    
class InvalidArguments(Exception):
    pass
    
class InvalidOptions(Exception):
    pass
    
class CLIInterpreter(object):

    Opts = ("", [])
    Usage = ""
    Defaults = {}
    MinArgs = 0

    def get_options(self):
        tup = self.Opts
        out = ("", [])
        if isinstance(tup, str):
            words = tup.split()
            if words:
                if words[0] == "--":
                    out = ("", words[1:])
                else:
                    out = (words[0], words[1:])
        elif isinstance(tup, list):
            out = ("", tup)
        else:
            assert isinstance(tup, tuple) and len(tup) == 2
            out = tup
        return out

    def make_opts_dict(self, opts):
        opts_dict = {}
        for opt, val in opts:
            existing = opts_dict.get(opt)
            if existing is None:
                opts_dict[opt] = val
            elif isinstance(existing, list):
                existing.append(val)
            else:
                opts_dict[opt] = [existing, val]
        out = self.Defaults.copy()
        out.update(opts_dict)
        return out

    def getopt(self, argv):
        short_opts, long_opts = self.get_options()
        try:
            opts, args = getopt.getopt(argv, short_opts, long_opts)
        except getopt.GetoptError:
            raise InvalidOptions()
        if len(args) < self.MinArgs:
            raise InvalidArguments()
        return self.make_opts_dict(opts), args
    
    # overridable
    def _run(self, command, context, argv, usage_on_empty = True, usage_on_unknown = True):
        return None
        
    
class CLICommand(CLIInterpreter):

    def _run(self, command, context, argv, usage_on_error = True):
        try:
            opts, args = self.getopt(argv)
        except (InvalidOptions, InvalidArguments):
            if usage_on_error:
                cmd = "" if not command else f"for {command}"
                print(f"Invalid arguments or options for {cmd}\n", file=sys.stderr)
                print(self.usage(), file=sys.stderr)
            else:
                raise
        return self(command, context, opts, args)

    def format_usage(self, first_indent, rest_indent):
        try:
            usage = self.Usage
        except AttributeError:
            usage = ""
        usage = usage.rstrip()
        if "\n" in usage:
            first_line, rest = usage.split("\n", 1)
            rest = rest.rstrip()
            first_line = first_line.strip()
            return [first_indent + first_line] + [rest_indent + l for l in textwrap.dedent(rest).split("\n")]
        else:
            return [first_indent + usage.strip()]
        
    def usage(self, first_indent="", rest_indent=None):
        if rest_indent is None:
            rest_indent = first_indent
        return "\n".join(self.format_usage(first_indent, rest_indent))

class CLI(CLIInterpreter):
    
    def __init__(self, *args, hidden=False):
        self.Hidden = hidden
        groups = []
        group = []
        group_name = ""
        i = 0
        while i < len(args):
            a = args[i]
            if a.endswith(":"):
                if group:
                    groups.append((group_name, group))
                group_name = a
                group = []
            else:
                w = a
                c = args[i+1]
                i += 1
                group.append((w, c))
            i += 1
        if group:
            groups.append((group_name, group))
        self.Groups = groups
            
    def add_group(self, title, commands):
        if (not title) and self.Groups:
            raise ValueError("Only first group can be unnamed")
        self.Groups.append((title, commands))
        
    # overridable
    def update_context(self, context, opts, args):
        return context
    
    def find_interpreter(self, word):
        interp = None
        for group_name, commands in self.Groups:
            for w, c in commands:
                if word == w:
                    interp = c
                    break
            if interp is not None:
                break
        #print(self.__class__.__name__, f".find_interpreter({word}) ->", interp)
        return interp

    def _run(self, command, context, argv, usage_on_error = True):
        try:
            opts, args = self.getopt(argv)
        except (InvalidOptions, InvalidArguments):
            if usage_on_error:
                cmd = "" if not command else f"for {command}"
                print(f"Invalid arguments or options for {cmd}\n", file=sys.stderr)
                print(self.usage(), file=sys.stderr)
                return
            else:
                raise

        if not args:
            if usage_on_error:
                print(self.usage(), file=sys.stderr)
                return
            else:
                raise EmptyCommandLine()
            

        #print(f"{self.__class__.__name__}._run(): argv:", argv, "  args:", args)

        context = self.update_context(context, opts, args)
        word, rest = args[0], args[1:]
        
        if word in ("help", "-h", "-?", "--help"):
            print(self.usage(long=True), file=sys.stderr())
        
        interp = self.find_interpreter(word)
        if interp is None:
            print(f"Unknown command {command} {word}\n", file=sys.stderr)
            if usage_on_error:
                indent = "" if not command else "  "
                print("Usage:" if not command else f"Usage for {command}:\n", 
                      self.usage(indent=indent),
                      file=sys.stderr)
                return
            else:
                raise UnknownCommand(word, argv)
        
        return interp._run(word, context, rest, usage_on_error = usage_on_error)
        
    def run(self, argv, context=None, usage_on_error = True):
        self._run("", context, argv, usage_on_error)

    def usage(self, headline="", as_list=False, long=True, end="", indent=""):

        if self.Hidden:
            return [] if as_list else ""
        
        out = []
        
        if headline:
            out.append(indent + headline)

        maxcmd = 0
        maxgroup = 0
        for group_name, interpreters in self.Groups:
            maxcmd = max(maxcmd, max(len(w) for (w, _) in interpreters))
            maxgroup = max(len(group_name), maxgroup)

        if not long:
            for group_name, interpreters in self.Groups:
                head = (f"%-{maxgroup}s: " % (group_name,)) if group_name else ""
            line = head + ",".join(w for w, i in interpreters)
            out.append(indent + line)
        else:
            for i, (group_name, interpreters) in enumerate(self.Groups):
                if group_name:
                    out.append(indent + group_name)
                fmt = f"%-{maxcmd}s %s"
                offset = "  " if group_name else ""
                for i, (word, interp) in enumerate(interpreters):
                    if isinstance(interp, CLI):
                        if not interp.Hidden:
                            out.append(indent + offset + word)
                            usage = interp.usage(headline="", indent=indent + offset + "    ", long=False)
                            out.append(usage)
                    elif isinstance(interp, CLICommand):
                        # assume CLICommand subclass
                        #usage = interp.usage(" "*(maxcmd-len(word)), indent + " "*(maxcmd+1))
                        #usage = interp.usage("", indent + " "*(maxcmd+1))
                        usage = interp.usage("", indent + "    ")
                        pre_word = "" if usage.strip().split(None, 1)[0] == word else word + " "
                        out.append(indent + pre_word + usage)
                        out.append("")
                    else:
                        raise ValueError("Unrecognized type of the interpreter: %s %s" % (type(interp), interp))
        #print(self, f": usage:{out}")
        if as_list:
            return out
        else:
            return "\n".join(out) + end
        
    def print_usage(self, headline="Usage:", head_paragraph = "", file=None):
        if file is None: file = sys.stderr
        head_paragraph = textwrap.dedent(head_paragraph).strip()
        if headline:
            print(headline, file=file)
        if head_paragraph:
            print(head_paragraph, file=file)
        usage = self.usage(headline=None)
        print(self.usage(headline=None), file=file)
        
