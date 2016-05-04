# Copyright 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
#
# This file is part of abkhazia: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Abkhazia is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with abkhazia. If not, see <http://www.gnu.org/licenses/>.
"""Implementation of the 'abkhazia features' command"""

from abkhazia.commands.abstract_command import AbstractRecipeCommand
import abkhazia.core.features as features
import abkhazia.utils as utils


class AbkhaziaFeatures(AbstractRecipeCommand):
    name = 'features'
    description = 'compute MFCC features and CMVN statistics'

    @classmethod
    def add_parser(cls, subparsers):
        """Return a parser for the align command"""
        # get basic parser init from AbstractCommand
        parser, dir_group = super(AbkhaziaFeatures, cls).add_parser(subparsers)

        parser.add_argument(
            '-j', '--njobs', type=int, metavar='<njobs>',
            default=cls._default_njobs(20),
            help="""number of jobs to launch for features computation, default is to
            launch %(default)s jobs.""")

        parser.add_argument(
            '--use-pitch', metavar='<true|false>', choices=['true', 'false'],
            default=utils.config.get('features', 'use-pitch'),
            help="""if true, compute pitch features along with MFCCs,
            default is %(default)s""")

        return parser

    @classmethod
    def run(cls, args):
        corpus, output_dir = cls.prepare_for_run(args)
        recipe = features.Features(corpus, output_dir, args.verbose)
        recipe.use_pitch = True if args.use_pitch == 'true' else False
        recipe.njobs = args.njobs
        recipe.create()
        recipe.run()