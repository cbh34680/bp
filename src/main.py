import sys
import json
import struct
import pprint
import itertools
import numbers
import argparse
import io
import collections.abc


TYPESIZE = {
    'x': 1,
    'c': 1,
    'b': 1,
    'B': 1,
    '?': 1,
    'h': 2,
    'H': 2,
    'i': 4,
    'I': 4,
    'l': 4,
    'L': 4,
    'q': 8,
    'Q': 8,
    # 'n'
    # 'N'
    # 'e'
    'f': 4,
    'd': 8,
    's': 1,
    # 'p'
    # 'P'
}


#def func_seek_set(f:io.BufferedReader, l:int, **kwargs):
#    f.seek(l)


FUNCMAP = {
    #'.seek_set': func_seek_set,
    '.seek_set': lambda f, l, **kwargs: f.seek(l),
}


def hir2indent(hir:list):
    return ''.join(itertools.repeat('\t', len(hir)))


def walk(seqs:dict, f:io.BufferedReader, g:dict, hir:list):
    for curr in seqs:
        name = curr['name']
        typ = curr['type']

        full_name = '/'.join(hir) + f'/{name}'
        l = curr.get('length') or 1

        if not isinstance(l, numbers.Number):
            l = g['vars'][l]

        if typ in FUNCMAP:
            func = FUNCMAP[typ]
            func(name=name, f=f, g=g, l=l, full_name=full_name)

        elif typ in TYPESIZE:
            tsize = TYPESIZE[typ]
            rsize = tsize * l

            #print(f"# full_name={full_name} name={name} type={typ} tsize={tsize} l={l} rsize={rsize}", file=sys.stderr)

            byts = f.read(rsize)
            vals = struct.unpack(f'={l}{typ}', byts)
            nvals = len(vals)

            if nvals == 0:
                # type: 'x'
                pass

            else:
                p_vals = vals

                if typ.isupper():
                    p_vals = tuple(map(hex, vals))

                if nvals == 1:
                    vals = vals[0]
                    p_vals = p_vals[0]

                p_vals = pprint.pformat(p_vals, width=sys.maxsize)

                if typ.isupper():
                    p_vals = p_vals.replace("'", '')

                print(f'{hir2indent(hir)}{name}: {p_vals}')

                if f'${full_name}' in g['refnames']:
                    g['vars'][f'${full_name}'] = vals

        elif typ in g['structs']:
            if l > 1:
                for i in range(l):
                    print(f'{hir2indent(hir)}{name}[{i}] - {f.tell()}')
                    walk(g['structs'][typ], f, g, hir + [ name + f"[{i}]" ])

            else:
                print(f'{hir2indent(hir)}{name} - {f.tell()}')
                walk(g['structs'][typ], f, g, hir + [ name ])

        else:
            raise IndexError(f'{typ}: type not found')


def coll_refnames(tree):
    if isinstance(tree, collections.abc.Mapping):
        for k, v in tree.items():
            if isinstance(v, collections.abc.Mapping) or isinstance(v, list) or isinstance(v, tuple):
                yield from coll_refnames(v)

            elif isinstance(v, str):
                if v[0] == '$':
                    yield v

    else:
        # list, tuple
        for v in tree:
            if isinstance(v, collections.abc.Mapping) or isinstance(v, list) or isinstance(v, tuple):
                yield from coll_refnames(v)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', required=True, help='spec json path')
    parser.add_argument('--data', required=True, help='binary data path')
    args = parser.parse_args()

    with (
        open(args.spec) as f_spec,
        open(args.data, 'rb') as f_data):

        spec = json.load(f_spec)

        refnames = set()
        for v in coll_refnames(spec):
            refnames.add(v)

        g = {'vars': {}, 'structs': spec['structs'], 'refnames': refnames}

        walk(spec['root'], f_data, g, [])

        print(f'# done. - {f_data.tell()}', file=sys.stderr)
        pprint.pprint(g['vars'])


if __name__ == '__main__':
    main()

# EOF
