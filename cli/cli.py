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
    
class CLICommand(object):

    Opts = ""
    Usage = ""
    Defaults = {}

    def run(self, command, argv, *params, **kwargs):
        short_opts = ""
        long_opts = []
        try:
            opts = self.Opts
        except AttributeError:
            pass
        if isinstance(opts, tuple):
            short_opts, long_opts = opts
        elif isinstance(opts, str):
            short_opts = opts
        elif isinstance(opts, list):
            long_opts = opts
        opts, args = getopt.getopt(argv, short_opts, long_opts)
        opts_dict = {}
        for opt, val in opts:
            existing = opts_dict.get(opt)
            if existing is None:
                opts_dict[opt] = val
            elif isinstance(existing, list):
                existing.append(val)
            else:
                opts_dict[opt] = [existing, val]
        out_opts = self.Defaults.copy()
        out_opts.update(opts_dict)
        return self(command, out_opts, args, *params, **kwargs)

    @classmethod
    def usage(cls, first_indent="", rest_indent=None):
        if rest_indent is None:
            rest_indent = first_indent
        try:
            usage = cls.Usage
        except AttributeError:
            usage = ""
        if "\n" in usage:
            first_line, rest = usage.split("\n", 1)
            first_line = first_line.strip()
            rest = textwrap.dedent(rest)
            return first_indent + first_line + "\n" + textwrap.indent(rest, rest_indent)
        else:
            return usage.strip()
        
    @classmethod
    def format_usage(cls, first_indent, rest_indent):
        try:
            usage = cls.Usage
        except AttributeError:
            usage = ""
        if "\n" in usage:
            first_line, rest = usage.split("\n", 1)
            rest = rest.rstrip()
            first_line = first_line.strip()
            return [first_indent + first_line] + [rest_indent + l for l in textwrap.dedent(rest).split("\n")]
        else:
            return [first_indent + usage.strip()]
        
    @classmethod
    def usage(cls, first_indent="", rest_indent=None):
        if rest_indent is None:
            rest_indent = first_indent
        return "\n".join(cls.format_usage(first_indent, rest_indent))

class CLI(object):
    
    def __init__(self, *args):
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
        
    def run(self, argv, *params, usage_on_empty = True, usage_on_unknown = True, **kwargs):
        
        if not argv:
            if usage_on_empty:
                print(self.usage(), file=sys.stderr)
                return
            else:
                raise EmptyCommandLine()
        
        word, rest = argv[0], argv[1:]
        
        if word in ("-h", "-?", "--help"):
            self.print_usage()
            return

        interp = None
        for group_name, commands in self.Groups:
            for w, c in commands:
                if word == w:
                    interp = c
                    break
            if interp is not None:
                break
        else:
            if usage_on_unknown:
                print(self.usage(), file=sys.stderr)
                return
            else:
                raise UnknownCommand(word, argv)
        
        if isinstance(interp, CLI):
            return interp.run(rest, *params, 
                        usage_on_empty = usage_on_empty, usage_on_unknown = usage_on_unknown,
                        **kwargs)
        else:
            return interp().run(word, rest, *params, **kwargs)

    def usage(self, as_list=False, headline="Usage:", end="", indent=""):
        out = []
        if headline:
            out.append(indent + headline)

        maxcmd = 0
        for group_name, interpreters in self.Groups:
            maxcmd = max(maxcmd, max(len(w) for (w, _) in interpreters))
        
        for i, (group_name, interpreters) in enumerate(self.Groups):
            if group_name:
                out.append(indent + group_name)
            fmt = f"%-{maxcmd}s %s"
            offset = "  " if group_name else ""
            for i, (word, interp) in enumerate(interpreters):
                #if i > 0:
                #    out.append("")
                if isinstance(interp, CLI):
                    out.append(indent + offset + word)
                    usage = interp.usage(headline="", indent=indent + offset + "  ")
                    out.append(usage)
                else:
                    # assume CLICommand subclass
                    #usage = interp.usage(" "*(maxcmd-len(word)), indent + " "*(maxcmd+1))
                    #usage = interp.usage("", indent + " "*(maxcmd+1))
                    usage = interp.usage("", indent + "  ")
                    out.append(indent + word + " " + usage)
                    out.append("")
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
        
