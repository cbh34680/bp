import argparse
import lark

# https://zenn.dev/tbsten/articles/d922514e548518
# https://developers.10antz.co.jp/archives/2007
# https://lark-parser.readthedocs.io/en/latest/grammar.html
# https://github.com/lark-parser/lark
# https://github.com/ligurio/lark-grammars


def types2format(types, num):
    format = None

    if num > 0:
        if 'char' in types:
            if 'unsigned' in types:
                format = 'b'
            else:
                if num == 1:
                    format = 'c'
                else:
                    format = 's'

        elif 'short' in types:
            format = 'h'

        elif 'float' in types:
            format = 'f'

        elif 'double' in types:
            format = 'd'

        else:
            xs = list(filter(lambda x: x == 'long', types))

            match len(xs):
                case 0:
                    format = 'i'
                case 1:
                    format = 'l'
                case _:
                    format = 'q'

    assert format is not None
    return format


#@lark.v_args(inline=True)
class MyTrans(lark.Transformer):

    def __init__(self):
        self.decls = []
        self.cur = {}
        self.aliases = {}


    def nativetypes(self, items):
        for item in items:
            if item.data in ('char', 'int', 'short', 'long', 'float', 'double', 'signed', 'unsigned'):
                self.cur.setdefault('types', [])
                self.cur['types'].append(item.data)


    @lark.v_args(inline=True)
    def declname(self, token):
        self.cur['name'] = token.value


    def declarrs(self, items):
        for item in items:
            self.cur.setdefault('num', 1)
            self.cur['num'] *= int(item.value)


    def resolve_alias(self, name, num=1):
        if name in self.aliases:
            alias = self.aliases[name]

            self.resolve_alias()

        pass


    def native(self, _):
        self.cur.setdefault('num', 1)
        num = self.cur['num']

        if num == 0:
            return

        types = self.cur['types']
        format = types2format(types, num)

        '''
        {
            "name": "mag_ELF",
            "type": "s",
            "length": 3
        },
        '''

        x = {
            'name': self.cur['name'],
            'type': format,
        }

        if num > 1:
            x['length'] = num

        self.decls.append(x)
        self.cur = {}


    def typedef(self, _):
        for decl in self.decls:
            self.aliases[decl['name']] = decl



def main():
    aparser = argparse.ArgumentParser()
    aparser.add_argument('--spec', required=True, help='lark grammer')
    aparser.add_argument('--inc', required=True, help='c/c++ header')
    args = aparser.parse_args()

    with (
        open(args.spec) as f_spec,
        open(args.inc) as f_inc
    ):
        parser = lark.Lark(f_spec, parser='lalr')
        tree = parser.parse(f_inc.read())
        print(tree.pretty())

        trans = MyTrans()
        trans.transform(tree)

    pass


if __name__ == '__main__':
    main()

# EOF
