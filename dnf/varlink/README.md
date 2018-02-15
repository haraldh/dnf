For Fedora 
```bash
$ sudo dnf install python3-varlink libvarlink-util
$ sudo dnf update https://kojipkgs.fedoraproject.org/packages/python-varlink/12/1.fc28/noarch/python3-varlink-12-1.fc28.noarch.rpm
$ git clone -b 2.7.5 https://github.com/haraldh/dnf.git
$ cd dnf
$ cmake . -DPYTHON_DESIRED:str=3 -DWITH_MAN=0 -DPYTHON_EXECUTABLE=/usr/bin/python3
$ make
$ ./bin/dnf-varlink-3 unix:@test &
$ varlink call unix:@test/com.redhat.packages.List '{}'
{
  "packages": [
    {
      "name": "ConsoleKit-libs",
      "version": {
        "architecture": "x86_64",
        "release": "9.fc22",
        "version": "0.4.5"
      }
    },
    {
      "name": "GConf2",
      "version": {
        "architecture": "x86_64",
        "release": "19.fc27",
        "version": "3.2.6"
      }
    },
    {
      "name": "GConf2-devel",
      "version": {
        "architecture": "x86_64",
        "release": "19.fc27",
        "version": "3.2.6"
      }
    },
    {
      "name": "GeoIP",
      "version": {
        "architecture": "x86_64",
        "release": "2.fc28",
        "version": "1.6.12"
      }
    },
    {
      "name": "GeoIP-GeoLite-data",
      "version": {
        "architecture": "noarch",
        "release": "1.fc28",
        "version": "2018.01"
      }
    },
```
