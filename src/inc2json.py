import argparse
import lark
import pprint

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
        self.temp = {}
        self.userdefs = {}

        self.declroot = {}
        self.declblock = {'..': self.declroot}



    def nativetypes(self, items):
        types = []

        for item in items:
            types.append(item.data)

        return types


    def declarrs(self, items):
        for item in items:
            self.temp.setdefault('num', 1)
            self.temp['num'] *= int(item.value)


    @lark.v_args(inline=True)
    def declarr(self, token):
        return int(token)


    @lark.v_args(inline=True)
    def declare(self, decl):
        self.declblock[decl['name']] = decl
        self.temp = {}
        return decl


    @lark.v_args(inline=True)
    def userdef(self, origname, declname, _):
        orig = self.userdefs[origname.value]
        num = orig['length'] * self.temp['num']

        return {
            'name': declname.value,
            'type': orig['type'],
            'length': num,
        }


    @lark.v_args(inline=True)
    def native(self, _, declname, *args):
        self.temp.setdefault('num', 1)
        num = self.temp['num']

        format = types2format(self.temp['types'], num)

        return {
            'name': declname.value,
            'type': format,
            'length': num,
        }


    def typedef(self, decl):
        pass



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

        pprint.pprint(trans.__dict__)
        pass

    pass


if __name__ == '__main__':
    main()

# EOF
