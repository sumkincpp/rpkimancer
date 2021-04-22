# PYTHON_ARGCOMPLETE_OK
#
# Copyright (c) 2021 Ben Maddison. All rights reserved.
#
# The contents of this file are licensed under the MIT License
# (the "License"); you may not use this file except in compliance with the
# License.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""rpki-augur command implementation."""

from __future__ import annotations

import contextlib
import functools
import logging
import os
import sys
import typing

from . import Args, BaseCommand, Return

if typing.TYPE_CHECKING:
    from rpkimancer.asn1 import Content

log = logging.getLogger(__name__)

WriteGenerator = typing.Generator[typing.Callable[["Content", str], None],
                                  None,
                                  None]


class Augur(BaseCommand):
    """Learn of the secrets carried within an RPKI signed object."""

    subcommand = "augur"
    usage = None

    def init_parser(self) -> None:
        """Set up command line argument parser."""
        self.parser.add_argument("path",
                                 metavar="<file-path>",
                                 help="Path to the signed object")
        self.parser.add_argument("--output", "-o",
                                 metavar="<output-path>",
                                 type=self._output, default=self._output(),
                                 help="Path to output file "
                                      "(default: STDOUT)")
        self.parser.add_argument("--signed-data", "-S",
                                 action="store_true", default=False,
                                 help="Print decoded SignedData structure")
        self.parser.add_argument("--no-econtent", "-E",
                                 action="store_true", default=False,
                                 help="Don't print decoded eContent")
        fmt = self.parser.add_mutually_exclusive_group()
        self.parser.set_defaults(fmt_method="to_asn1")
        fmt.add_argument("--asn1", "-A", dest="fmt_method",
                         action="store_const", const="to_asn1",
                         help="Output ASN.1 data syntax")
        fmt.add_argument("--json", "-J", dest="fmt_method",
                         action="store_const", const="to_json",
                         help="Output JSON/JER encoded data")

    def run(self, args: Args) -> Return:
        """Run with the given arguments."""
        log.info("setting up rpkimancer library objects")
        from ..sigobj import from_ext
        log.info(f"trying to read signed object from {args.path}")
        with open(args.path, "rb") as f:
            data = f.read()
        _, ext = os.path.splitext(args.path)
        log.info(f"trying to determine object type from file extension {ext}")
        object_cls = from_ext(ext)
        log.info(f"trying to deserialise to {object_cls}")
        obj = object_cls.from_der(data)
        with args.output as write:
            if args.signed_data:
                write(obj, args.fmt_method)
            if not args.no_econtent:
                write(obj.econtent, args.fmt_method)
        return None

    @staticmethod
    @contextlib.contextmanager
    def _output(path: typing.Optional[str] = None) -> WriteGenerator:

        def _write(obj: Content, fmt_method: str, f: typing.TextIO) -> None:
            func = getattr(obj, fmt_method)
            f.write(func())

        if path is None:
            yield functools.partial(_write, f=sys.stdout)
        else:
            with open(path, "w") as f:
                yield functools.partial(_write, f=f)
