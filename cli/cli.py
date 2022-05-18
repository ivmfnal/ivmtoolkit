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
    def format_usage(cls, indent="    "):
        try:
            usage = cls.Usage
        except AttributeError:
            usage = ""
        
        if "\n" in usage:
            first_line, rest = usage.split("\n", 1)
            first_line = first_line.strip()
            rest = textwrap.dedent(rest)
            return first_line + "\n" + textwrap.indent(rest, indent)
        else:
            return usage.strip()
        
    
class CLI(object):
    
    def __init__(self, *args):
        #
        # commands:
        # [
        #    ("word", CommandClass), ...
        # ]
        #
        # groups:
        # [
        #    ("groups name", commands),
        # ]
        #
        
        groups = []
        group = []
        group_name = ""
        i = 0
        while i < len(args):
            a = args[i]
            if a.endswith(":"):
                if group:
                    groups.append((group_name, group))
                group_name = a[:-1]
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
            
    def add_group(self, group_name, commands):
        self.Groups.append((group_name, commands))
        
    def execute(self, argv, *params, usage_on_empty = True, usage_on_unknown = True, **kwargs):
        
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

        cmd_class = None
        for group_name, commands in self.Groups:
            for w, c in commands:
                if word == w:
                    cmd_class = c
                    break
            if cmd_class is not None:
                break
        else:
            if usage_on_unknown:
                print(self.usage(), file=sys.stderr)
                return
            else:
                raise UnknownCommand(word, argv)
        
        return cmd_class().run(word, rest, *params, **kwargs)

    def usage(self, as_list=False, headline="Usage:", end=""):
        out = []
        if headline:
            out.append(headline)
        maxcmd = 0
        for group_name, commands in self.Groups:
            maxcmd = max(maxcmd, max(len(w) for (w, _) in commands))
        
        for i, (group_name, commands) in enumerate(self.Groups):
            if i > 0:
                out.append("")
            out.append(group_name)
            fmt = f"%-{maxcmd}s %s"
            if group_name:
                fmt = "  " + fmt
            for word, cmd in commands:
                usage = cmd.format_usage()
                out.append(fmt % (word, usage))
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
        print(self.usage(headline=None), file=file)
        
class CommandA(CLICommand):
    
    Opts = "vc:"
    Usage = """[-v] [-c <config>]
            -c <config> - config file
            -v          - verbose output
    """
    
    def __call__(self, cmd, opts, args, x, y):
        print("Command:", cmd, "  opts:", opts, "  args:", args, "  x:", x, "  y:", y)

if __name__ == "__main__":
    import sys
    cli = CLI(
            "b", CommandA,
            "extra:",
            "a", CommandA
    )
    x = "X"
    y = "Y"

    cli.execute(sys.argv[1:], x, y, usage_on_unknown=True)