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


pp = pprint.PrettyPrinter(width=110)

def types2format(types, num):
    format = None

    natives = tuple(filter(lambda x: x not in ('const', 'ptr'), types))

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

    if 'ptr' in types:
        format = 'P'

    return format


def gen_decl(name:str, type, length, memo=None):

    if memo is None:
        memo = ''

    return {
        'name': name,
        'type': type,
        'length': length,
        'memo': memo,
    }


def is_iter(x:collections.abc.Iterable):
    return isinstance(x, collections.abc.Iterable) and not isinstance(x, str)


def head_text(tree:lark.Tree):
    return head_val(tree, '')

def head_val(tree:lark.Tree, default):
    return tree.children[0].value if len(tree.children) > 0 else default


#@lark.v_args(inline=True)
class MyTrans(lark.Transformer):
    def __init__(self):
        self.db = {
            'typedef': {},
            'struct': {},
            'define': {},
        }


    @lark.v_args(inline=True)
    def define(self, name, val):
        self.db['define'][name.value] = val



    # typedef
    @lark.v_args(inline=True)
    def typedef(self, tree):

        for decl in tree.children:
            name = decl['name']

            assert name != '', 'ERROR: need typename'
            assert name not in self.db['typedef'], f'ERROR: {name} is not in db'

            self.db['typedef'][name] = decl


    # struct {}
    @lark.v_args(inline=True)
    def usertype(self, tagname, decls, typename, num):

        '''
        https://www.tutorialspoint.com/How-to-join-list-of-lists-in-python

        # input list of lists (nested list)
        input_list = [["tutorialspoint", "python"], [2, 6, 7], [9, 5, 12, 7]]
        print(input_list)

        # Getting each element from nested Lists and storing them in a new list using list comprehension
        resultList = [element for nestedlist in input_list for element in nestedlist]

        # printing the resultant list after joining the list of lists
        print("Resultant list after joining list of lists = ", resultList)
        '''
        type = tuple([ x for decl in decls.children for x in decl.children ])
        #assert isinstance(type, collections.abc.Iterable)

        tagname = head_text(tagname)
        name = head_text(typename)

        memo = f'(U)t={tagname},n={name},m=' + f'{len(type)}'

        decl = gen_decl(name, type, num, memo)
        if tagname != '':
            self.db['struct'][tagname] = decl

        return decl


    # __int64_t, ...
    @lark.v_args(inline=True)
    def alias(self, orgname, name, num):

        org = self.db['typedef'][orgname]

        num *= org['length']
        memo = org['memo'] + f', (A){orgname}'

        return gen_decl(name.value, org['type'], num, memo)


    # char, int, ...
    @lark.v_args(inline=True)
    def stdtype(self, types, name, num):

        format = types2format(types, num)
        memo = '(S)' + ' '.join(types)

        return gen_decl(name.value, format, num, memo)

    def builtins(self, items):
        return tuple(map(lambda x: x.data, items))


    # [10]
    #@lark.v_args(inline=False)
    def declarrs(self, items):
        if len(items) == 0:
            return 1

        return functools.reduce(operator.mul, items)


    @lark.v_args(inline=True)
    def raw(self, v):
        return v

    @lark.v_args(inline=True)
    def expr(self, token:lark.Token):
        val = self.db['define'].get(token.value)
        val = token.value if val is None else val

        return int(val)


    @lark.v_args(inline=True)
    def expr_add(self, a, b):
        return a + b

    @lark.v_args(inline=True)
    def expr_sub(self, a, b):
        return a - b

    @lark.v_args(inline=True)
    def expr_mul(self, a, b):
        return a * b



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

        pp.pprint(self.__dict__)

        #out = {}
        #for decl in filter(lambda x: is_iter(x['type']), self.db['typedef'].values()):
        #    out[decl['name']] = decl['type']

        structs = filter(lambda x: is_iter(x['type']), self.db['typedef'].values())
        #out = { x['name']: x['type'] for x in structs }
        out = { x['name']: type2out(x['type']) for x in structs }

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
