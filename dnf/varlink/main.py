# __init__.py
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


import itertools
import logging

logger = logging.getLogger('dnf')

import os
import stat

import dnf
import varlink
from types import SimpleNamespace

service = varlink.Service(
    vendor='Red Hat',
    product='Packages',
    version='1',
    interface_dir=os.path.dirname(__file__)
)


class ActionFailed(varlink.VarlinkError):
    def __init__(self, reason):
        varlink.VarlinkError.__init__(self,
                                      {'error': 'com.redhat.packages.ActionFailed',
                                       'parameters': {'field': reason}})


class BaseVarlink(dnf.Base):
    """This is the base class for yum cli."""

    def __init__(self, conf=None):
        conf = conf or dnf.conf.Conf()
        super(BaseVarlink, self).__init__(conf=conf)

    def returnPkgLists(self, pkgnarrow='all', patterns=None,
                       installed_available=False, reponame=None):
        """Return a :class:`dnf.yum.misc.GenericHolder` object containing
        lists of package objects that match the given names or wildcards.

        :param pkgnarrow: a string specifying which types of packages
           lists to produce, such as updates, installed, available, etc.
        :param patterns: a list of names or wildcards specifying
           packages to list
        :param installed_available: whether the available package list
           is present as .hidden_available when doing all, available,
           or installed
        :param reponame: limit packages list to the given repository

        :return: a :class:`dnf.yum.misc.GenericHolder` instance with the
           following lists defined::

             available = list of packageObjects
             installed = list of packageObjects
             upgrades = tuples of packageObjects (updating, installed)
             extras = list of packageObjects
             obsoletes = tuples of packageObjects (obsoleting, installed)
             recent = list of packageObjects
        """

        done_hidden_available = False
        done_hidden_installed = False
        if installed_available and pkgnarrow == 'installed':
            done_hidden_available = True
            pkgnarrow = 'all'
        elif installed_available and pkgnarrow == 'available':
            done_hidden_installed = True
            pkgnarrow = 'all'

        ypl = self._do_package_lists(
            pkgnarrow, patterns, ignore_case=True, reponame=reponame)
        if self.conf.showdupesfromrepos:
            ypl.available += ypl.reinstall_available

        if installed_available:
            ypl.hidden_available = ypl.available
            ypl.hidden_installed = ypl.installed
        if done_hidden_available:
            ypl.available = []
        if done_hidden_installed:
            ypl.installed = []
        return ypl


@service.interface('com.redhat.packages')
class Example:
    def List(self, packages=None, _more=False):
        if _more:
            return varlink.InvalidParameter('more')

        base = BaseVarlink()

        if not packages:
            base.fill_sack(load_system_repo='auto',
                           load_available_repos=True)

            lists = base.returnPkgLists(pkgnarrow='installed')
            pkgs = itertools.chain.from_iterable(lists.all_lists().values())
            ret = []
            for p in pkgs:
                r = SimpleNamespace()
                r.version = SimpleNamespace()
                r.name = p.name
                if p.e > 0:
                    r.version.epoch = p.e
                r.version.version = p.v
                r.version.release = p.r
                r.version.architecture = p.arch
                ret.append(r)
        return {"packages": ret}


def main(args):
    if len(args) < 1:
        print('missing address parameter')
        return 1

    listen_fd = None

    try:
        if stat.S_ISSOCK(os.fstat(3).st_mode):
            listen_fd = 3
    except OSError:
        pass

    with varlink.SimpleServer(service) as s:
        print("Listening on", args[0])
        try:
            s.serve(args[0], listen_fd=listen_fd)
        except KeyboardInterrupt:
            pass
    return 0
