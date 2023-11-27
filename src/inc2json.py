import argparse
import lark
import pprint
import operator
import functools
import collections.abc
import json

# https://zenn.dev/tbsten/articles/d922514e548518
# https://developers.10antz.co.jp/archives/2007
# https://lark-parser.readthedocs.io/en/latest/grammar.html
# https://github.com/lark-parser/lark
# https://github.com/ligurio/lark-grammars


pp = pprint.PrettyPrinter(width=110, indent=2)

def types2format(types, num):
    format = None

    natives = tuple(filter(lambda x: x not in ('const', '*'), types))

    if 'char' in natives:
        if 'unsigned' in natives:
            format = 'B'
        else:
            if num == 1:
                format = 'c'
            else:
                format = 's'

    elif 'short' in natives:
        format = 'H' if 'unsigned' in natives else 'h'

    elif 'float' in natives:
        format = 'f'

    elif 'double' in natives:
        format = 'd'

    else:
        xs = tuple(filter(lambda x: x == 'long', natives))

        match len(xs):
            case 0:
                # 4 byte (int)
                format = 'I' if 'unsigned' in natives else 'i'
            #case 1:
            #    format = 'L' if 'unsigned' in natives else 'l'
            case _:
                # 8 byte (long, long long)
                format = 'Q' if 'unsigned' in natives else 'q'

    assert format is not None

    if '*' in types:
        format = 'P'

    return format


def gen_decl(name:str, type, length=1, *, tag=None, memo=None):

    if tag is None:
        tag = ''

    if memo is None:
        memo = ''

    decl = {
        'name': name,
        'type': type,
        'length': length,
        'tag': tag,
        'memo': memo,
    }

    return decl


def is_iter(x:collections.abc.Iterable):
    return isinstance(x, collections.abc.Iterable) and not isinstance(x, str)


def head_text(tree:lark.Tree):
    return head_val(tree, '')

def head_val(tree:lark.Tree, default):
    return tree.children[0].value if len(tree.children) > 0 else default


@lark.v_args(inline=True)
class MyTrans(lark.Transformer):
    from operator import add, mul, sub, truediv as div

    def __init__(self):
        self.db = {
            'typedef': {},
            'struct': {},
            'define': {},
            'uniqid': 0,
        }


    def define(self, name, val):
        self.db['define'][name.value] = val


    # typedef
    def typedef(self, decl):
        name = decl['name']

        assert name != '', 'ERROR: need typename'
        assert name not in self.db['typedef'], f'ERROR: {name} is not in db'

        self.db['typedef'][name] = decl


    # struct tag name
    def usertyperef(self, tagname, name, num):
        decl = self.db['struct'][tagname]

        return {
            'name': name.value,
            'type': tagname.value,
            'length': num,
            'memo': decl['memo'] + f' (R){name}',
        }


    # struct tag { char c; } name [1]
    def usertypedecl(self, tagname, decls, typename, num):
        type = decls.children

        tagname = head_text(tagname)
        name = head_text(typename)
        memo = f'(U)t={tagname},n={name},m=' + f'{len(type)}'

        decl = gen_decl(name, type, num, tag=tagname, memo=memo)
        if tagname != '':
            self.db['struct'][tagname] = decl

        return decl


    # __int64_t, ...
    def alias(self, orgname, name, num):
        org = self.db['typedef'][orgname.value]

        num *= org['length']
        memo = org['memo'] + f', (A){orgname.value}'

        return gen_decl(name.value, org['type'], num, memo=memo)


    # char, int, ...
    def stdtype(self, types, name, num):
        format = types2format(types, num)
        memo = '(S)' + ' '.join(types)

        return gen_decl(name.value, format, num, memo=memo)

    @lark.v_args(inline=False)
    def builtins(self, tokens):
        return tuple(map(lambda x: x.value, tokens))


    # [10]
    @lark.v_args(inline=False)
    def declarrs(self, nums):
        if len(nums) == 0:
            return 1

        return functools.reduce(operator.mul, nums)

    atoi = int
    id = lambda _, v: v

    def var(self, token:lark.Token):
        return self.db['define'][token.value]


    def print(self):
        def type2out(decls):
            ret = []

            for org in decls:
                dst = {
                    'name': org['name'],
                    'type': org['type'],
                }

                if org['type'] == 's' or org['length'] > 1:
                    dst['length'] = org['length']

                ret.append(dst)

            return ret

        #pp.pprint(self.__dict__)

        #out = {}
        #for decl in filter(lambda x: is_iter(x['type']), self.db['typedef'].values()):
        #    out[decl['name']] = decl['type']

        out1 = { k: type2out(v['type']) for k, v in self.db['struct'].items() }

        structs = filter(lambda x: is_iter(x['type']), self.db['typedef'].values())
        out2 = { v['name']: type2out(v['type']) for v in structs }

        out = out1 | out2
        print(json.dumps(out, indent=2))


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
        #print(tree.pretty())

        trans = MyTrans()
        trans.transform(tree)

        #pp.pprint(trans.__dict__)

        trans.print()


if __name__ == '__main__':
    main()

# EOF
