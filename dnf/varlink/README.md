```bash
$ cmake . -DPYTHON_DESIRED:str=3 -DWITH_MAN=0 -DPYTHON_EXECUTABLE=/usr/bin/python3
$ make
$ ./bin/dnf-varlink-3 unix:@test
$ varlink call unix:@test/com.redhat.packages.List '{}'
```
