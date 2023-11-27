# binary print

*run*
```
$ python3 src/inc2json.py --spec inc2json.lark --inc elf-part.h > elf64.json

* edit elf64.json ('main' block)

$ python3 src/binprt.py --spec elf64.json --data a64.out
```
