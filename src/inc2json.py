import argparse
import lark
import pprint
import operator
import functools

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
        pass


    @lark.v_args(inline=True)
    def usertype(self, tagname, decls, typename):
        pass




    @lark.v_args(inline=True)
    def stdtype(self, types, name, num):

        format = types2format(types, num)

        return {
            'name': name.value,
            'type': format,
            'length': num,
        }

    def builtins(self, items):
        return list(map(lambda x: x.data, items))


    def declarrs(self, items):
        if len(items) == 0:
            return 1

        return functools.reduce(operator.mul, items)

    @lark.v_args(inline=True)
    def declarr(self, token):
        return int(token)



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
