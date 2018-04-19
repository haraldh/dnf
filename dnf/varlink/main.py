# main.py
# dnf.varlink
#
# Copyright (C) 2018 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#


import logging

logger = logging.getLogger('dnf')

import os
import getopt
import sys
import dnf
import dnf.cli
import varlink
import itertools
from types import SimpleNamespace

service = varlink.Service(
    vendor='Red Hat',
    product='Packages',
    version='1',
    interface_dir=os.path.dirname(__file__),
    namespaced=True
)


class ListPatternError(varlink.VarlinkError):
    def __init__(self, reason):
        varlink.VarlinkError.__init__(self,
                                      {'error': 'com.redhat.packages.ListPatternError'})


class ServiceRequestHandler(varlink.RequestHandler):
    service = service


@service.interface('com.redhat.packages')
class DnfVarlinkService(dnf.Base):
    def __init__(self):
        super().__init__()
        cli = dnf.cli.Cli(self)
        cli._read_conf_file()
        self.init_plugins(cli=cli)
        self.pre_configure_plugins()
        self.read_all_repos()
        self.configure_plugins()
        self.fill_sack()

    def List(self, packages=None, _more=False):

        def search_pattern(x):
            p = x.name
            if hasattr(x, "version"):
                # FIXME:
                if hasattr(x.version, "version"):
                    p += "-" + x.version.version

                    if hasattr(x.version, "release"):
                        p += "-" + x.version.release
                    else:
                        p += "-*"

                if hasattr(x.version, "architecture"):
                    p += "." + x.version.architecture
            return p

        def dnf2varlink_packages(p):
            r = SimpleNamespace()
            r.version = SimpleNamespace()
            r.name = p.name
            if p.e > 0:
                r.version.epoch = p.e
            r.version.version = p.v
            r.version.release = p.r
            r.version.architecture = p.arch
            return r

        if _more:
            return varlink.InvalidParameter('more')

        patterns = None
        all_or_installed = "all"
        if packages and len(packages) > 0:
            try:
                patterns = list(map((lambda x: search_pattern(x)), packages))
            except:
                return ListPatternError()
            # FIXME: select source for every package
            if (hasattr(packages[0], "installed") and packages[0].installed
                    and hasattr(packages[0], "available") and packages[0].available):
                all_or_installed = "all"
            elif hasattr(packages[0], "installed") and packages[0].installed:
                all_or_installed = "installed"
            elif hasattr(packages[0], "available") and packages[0].available:
                all_or_installed = "available"

        lists = self._do_package_lists(all_or_installed, patterns, ignore_case=True, reponame=None)
        ret = []
        seen = []
        for p in itertools.chain.from_iterable(lists.all_lists().values()):
            if p in seen:
                continue

            r = dnf2varlink_packages(p)
            r.installed = p in lists.installed
            r.available = (p in lists.available) or (p in lists.reinstall_available)
            ret.append(r)
            seen.append(p)

        return {"packages": ret}


def run_server(address):
    with varlink.ThreadingServer(address, ServiceRequestHandler) as server:
        print("Listening on", server.server_address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def usage():
    print('Usage: %s [--varlink=<varlink address>]' % sys.argv[0], file=sys.stderr)


def main(sysargs):
    print("main", file=sys.stderr)
    try:
        opts, args = getopt.getopt(sysargs, "", ["help", "varlink="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    address = None
    client_mode = False

    for opt, arg in opts:
        if opt == "--help":
            usage()
            sys.exit(0)
        elif opt == "--varlink":
            address = arg

    if not address:
        usage()
        sys.exit(2)

    run_server(address)

    sys.exit(0)
