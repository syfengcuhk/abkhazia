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
"""Implementation of the 'abkhazia prepare' command"""

import argparse
import os
import shutil
import textwrap

import abkhazia.utils as utils
from abkhazia.core.corpus import Corpus
from abkhazia.commands.abstract_command import AbstractCommand

# import all the corpora preparators TODO simplify those imports
from abkhazia.prepare.aic_preparator import AICPreparator
from abkhazia.prepare.buckeye_preparator import BuckeyePreparator
from abkhazia.prepare.childes_preparator import ChildesPreparator
from abkhazia.prepare.csj_preparator import CSJPreparator
from abkhazia.prepare.librispeech_preparator import LibriSpeechPreparator
from abkhazia.prepare.xitsonga_preparator import XitsongaPreparator

from abkhazia.prepare.globalphone_abstract_preparator import (
    AbstractGlobalPhonePreparator)
from abkhazia.prepare.globalphone_mandarin_preparator import (
    MandarinPreparator)
from abkhazia.prepare.globalphone_vietnamese_preparator import (
    VietnamesePreparator)

from abkhazia.prepare.wsj_preparator import (
    WallStreetJournalPreparator,
    JournalistReadPreparator,
    JournalistSpontaneousPreparator,
    MainReadPreparator)


class AbstractFactory(object):
    """The Factory class runs a corpus preparator from command-line arguments

    A Factory class is dedicated to a single corpus preparator. It
    does the following things: TODO update

    * add_parser(): define and return an argument parser for the preparator
    * init_preparator(): instanciates the preparator and return it
    * run(): wrap the 2 previous functions, called from AbkhaziaPrepare

    """
    preparator = NotImplemented
    """The corpus preparator attached to the factory"""

    @staticmethod
    def format_url(url, sep='\n'):
        """Return a string from the string (or list of strings) 'url'"""
        if isinstance(url, str):
            return url
        else:
            return sep.join(url)

    @classmethod
    def long_description(cls):
        """Return a multiline description of the corpus being prepared"""
        return (
            'abkhazia corpus preparation for the ' +
            cls.preparator.description +
            '\n\ncorpus description:\n' +
            '  ' + cls.format_url(cls.preparator.url, '\n  ') +
            '\n\n' +
            cls.preparator.long_description.replace('    ', '  '))

    @classmethod
    def default_output_dir(cls):
        """Return the default output directory for corpus preparation

        This directory is 'data-directory'/'name', where
        'data-directory' is read from the abkhazia configuration file
        and 'name' is self.name

        """
        return os.path.join(
            utils.config.get('abkhazia', 'data-directory'),
            cls.preparator.name)

    @classmethod
    def add_parser(cls, subparsers):
        """Return a default argument parser for corpus preparation"""
        parser = subparsers.add_parser(cls.preparator.name)
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.description = textwrap.dedent(cls.long_description())

        group = parser.add_argument_group('directories')

        default_input_dir = cls.preparator.default_input_dir()
        if default_input_dir is not None:
            group.add_argument(
                '-i', '--input-dir', metavar='<input-dir>',
                default=default_input_dir,
                help='root directory of the raw corpus distribution, '
                '(default readed from configuration file is %(default)s)')

        else:
            group.add_argument(
                'input_dir', metavar='<input-dir>',
                help='root directory of the raw corpus distribution')

        group.add_argument(
            '-o', '--output-dir', metavar='<output-dir>', default=None,
            help='output directory, the prepared corpus is created in '
            '<output-dir>/data. If not specified use {}.'
            .format(cls.default_output_dir()))

        parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='display more messages to stdout')

        parser.add_argument(
            '-f', '--force', action='store_true',
            help='if specified, overwrite the output directory '
            '<output-dir>/data. If not specified but the directory exists, '
            'the program detects desired wav files already present and '
            'do not convert them again.')

        parser.add_argument(
            '-j', '--njobs', type=int, default=4, metavar='<njobs>',
            help='number of jobs to launch when doing parallel '
            'computations (mainly for wav conversion). '
            'Default is to launch %(default)s jobs.')

        group = parser.add_argument_group('validation options')
        group = group.add_mutually_exclusive_group()
        group.add_argument(
            '--no-validation', action='store_true',
            help='disable the corpus validation step (do only preparation)')
        group.add_argument(
            '--only-validation', action='store_true',
            help='disable the corpus preparation step (do only validation)')

        if cls.preparator.audio_format == 'wav':
            parser.add_argument(
                '--copy-wavs', action='store_true',
                help='the audio files of this corpus are already in wav. '
                'By default abkhazia will import them as symbolic links, '
                'use this option to force copy')

        return parser

    @classmethod
    def get_output_dir(cls, args, prep=None):
        """Return the preparator output directory <output-dir>/data

        if the --force option have been specified, delete
        <output-dir>/data before returning it.

        """
        if prep is None:
            prep = cls.preparator

        output_dir = (cls.default_output_dir()
                      if args.output_dir is None
                      else args.output_dir)

        _dir = os.path.join(output_dir, 'data')
        if args.force and os.path.exists(_dir):
            print 'removing {}'.format(_dir)
            shutil.rmtree(_dir)

        return output_dir

    @classmethod
    def init_preparator(cls, args):
        """Return an initialized preparator from parsed arguments"""
        data_dir = cls.get_output_dir(args)
        wavs_dir = os.path.join(data_dir, 'wavs')
        log = utils.get_log(
            os.path.join(data_dir, 'data_preparation.log'), args.verbose)

        if cls.preparator.audio_format == 'wav':
            prep = cls.preparator(
                args.input_dir, wavs_dir, log, args.copy_wavs)
        else:
            prep = cls.preparator(args.input_dir, wavs_dir, log)
        return prep

    @classmethod
    def _run_preparator(cls, args, preparator):
        if not args.only_validation:
            # initialize corpus from raw with it's preparator
            corpus = preparator.prepare()
        else:
            # corpus already prepared, load it
            corpus = Corpus.load(args.corpus)

        if not args.no_validation:
            # raise if the corpus is not in correct abkhazia format
            corpus.validate(args.njobs, preparator.log)

        # save the corpus to the output directory
        output_dir = os.path.join(
            cls.preparator.default_output_dir()
            if args.output_dir is None else args.output_dir,
            'data')
        corpus.save(output_dir)

    @classmethod
    def run(cls, args):
        """Initialize, validate and save a corpus from command line args"""
        cls._run_preparator(args, cls.init_preparator(args))


class AbstractFactoryWithCMU(AbstractFactory):
    """Preparation for corpora relying of the CMU dictionary"""
    @classmethod
    def add_parser(cls, subparsers):
        parser = super(AbstractFactoryWithCMU, cls).add_parser(subparsers)

        parser.add_argument(
            '--cmu-dict', default=None, metavar='<cmu-dict>',
            help='the CMU dictionary file to use for lexicon generation. '
            'If not specified use {}'.format(cls.preparator.default_cmu_dict))

        return parser

    @classmethod
    def init_preparator(cls, args):
        output_dir = cls.get_output_dir(args)
        return cls.preparator(
            args.input_dir, args.cmu_dict,
            output_dir, args.verbose, args.njobs)


class BuckeyeFactory(AbstractFactory):
    preparator = BuckeyePreparator


class XitsongaFactory(AbstractFactory):
    preparator = XitsongaPreparator


class CSJFactory(AbstractFactory):
    preparator = CSJPreparator


class ChildesFactory(AbstractFactory):
    preparator = ChildesPreparator


class AICFactory(AbstractFactoryWithCMU):
    preparator = AICPreparator


class LibriSpeechFactory(AbstractFactoryWithCMU):
    preparator = LibriSpeechPreparator

    # list of the LibriSpeech subcorpora. TODO this is actually
    # hard-coded to present a selection on --help. See if we can get
    # the selection at runtime by scanning input_dir...
    selection = ['dev-clean', 'dev-other',
                 'test-clean', 'test-other',
                 'train-clean-100', 'train-clean-360']

    @classmethod
    def add_parser(cls, subparsers):
        selection_descr = ', '.join(
            [str(i+1) + ' is ' + cls.selection[i]
             for i in range(len(cls.selection))])

        parser = super(LibriSpeechFactory, cls).add_parser(subparsers)

        parser.add_argument(
            '-s', '--selection', default=None,
            metavar='<selection>', type=int,
            help='the subpart of LibriSpeech to prepare. If not specified, '
            'prepare the entire corpus. Choose <selection> in {}. ('
            .format(range(1, len(cls.selection)+1)) + selection_descr + ')')

        parser.add_argument(
            '-l', '--librispeech-dict', default=None,
            help='the librispeech-lexicon.txt file at the root '
            'of the LibriSpeech distribution. '
            'If not specified, guess it from <input-dir>')

        return parser

    @classmethod
    def init_preparator(cls, args):
        selection = (None if args.selection is None
                     else cls.selection[args.selection-1])

        output_dir = cls.get_output_dir(args)

        return cls.preparator(
            args.input_dir, selection,
            args.cmu_dict, args.librispeech_dict,
            output_dir, args.verbose, args.njobs)


class WallStreetJournalFactory(AbstractFactoryWithCMU):
    """Instanciate and run one of the WSJ preparators from input arguments"""
    preparator = WallStreetJournalPreparator

    # mapping of the three WSJ specialized preparators
    selection = [
        ('journalist-read', JournalistReadPreparator),
        ('journalist-spontaneous', JournalistSpontaneousPreparator),
        ('main-read', MainReadPreparator)
    ]

    @classmethod
    def add_parser(cls, subparsers):
        selection_descr = ', '.join([
            str(i+1) + ' is ' + cls.selection[i][0]
            for i in range(len(cls.selection))])

        parser = super(WallStreetJournalFactory, cls).add_parser(subparsers)

        parser.add_argument(
            '-s', '--selection', default=None,
            metavar='<selection>', type=int,
            choices=range(1, len(cls.selection)+1),
            help='the subpart of WSJ to prepare. If not specified, '
            'prepare the entire corpus. Choose <selection> in {} ('
            .format(range(1, len(cls.selection)+1)) + selection_descr + '). '
            'If <selection> is specified but not <output-dir>, the selection '
            'name will be appended to the default output directory (e.g. for '
            '-s 1 it will be .../wsj-journalist-read instead of .../wsj).')

        return parser

    @classmethod
    def init_preparator(cls, args):
        # select the preparator
        preparator = (cls.preparator if args.selection is None
                      else cls.selection[args.selection-1][1])

        output_dir = cls.get_output_dir(args)

        return preparator(
            args.input_dir, args.cmu_dict,
            output_dir, args.verbose, args.njobs)


class GlobalPhoneFactory(AbstractFactory):
    preparator = AbstractGlobalPhonePreparator

    # all the supported languages mapped to their preparators
    preparators = {
        'mandarin': MandarinPreparator,
        'vietnamese': VietnamesePreparator
    }

    @classmethod
    def add_parser(cls, subparsers):
        """Overload of the AbstractPreparator.parser for GlobalPhone"""
        # add a language selection option to the arguments parser
        parser = super(GlobalPhoneFactory, cls).add_parser(subparsers)

        parser.add_argument(
            '-l', '--language', nargs='+', metavar='<language>',
            default=cls.preparators.keys(),
            choices=cls.preparators.keys(),
            help='specify the languages to prepare in {}, '
            'if this option is not specified prepare all the '
            'supported languages. '.format(cls.preparators.keys()) +
            'Actually only Vietnamese and Mandarin are supported '
            'by abkhazia.')

        return parser

    @classmethod
    def init_preparator(cls, args):
        preps = []
        for l in args.language:
            prep = cls.preparators[l]
            output_dir = cls.get_output_dir(args, prep)
            preps.append(
                prep(args.input_dir, output_dir, args.verbose, args.njobs))
        return preps

    @classmethod
    def run(cls, args):
        for prep in cls.init_preparator(args):
            cls._run_preparator(args, prep)


class AbkhaziaPrepare(AbstractCommand):
    name = 'prepare'
    description = 'prepare a speech corpus for use with abkhazia'

    supported_corpora = dict((c.preparator.name, c) for c in (
        AICFactory,
        BuckeyeFactory,
        ChildesFactory,
        CSJFactory,
        GlobalPhoneFactory,
        LibriSpeechFactory,
        WallStreetJournalFactory,
        XitsongaFactory
    ))

    @classmethod
    def describe_corpora(cls):
        """Return a list of strings describing the supported corpora"""
        return ['{} - {}'.format(
            # librispeech is the longest corpus name so the desired
            # key length is len('librispeech ') == 12
            key + ' '*(12 - len(key)),
            value.preparator.description)
                for key, value in sorted(cls.supported_corpora.iteritems())]

    @classmethod
    def add_parser(cls, subparsers):
        # get basic parser init from AbstractCommand
        parser = super(AbkhaziaPrepare, cls).add_parser(subparsers)
        parser.formatter_class = argparse.RawTextHelpFormatter
        parser.description = textwrap.dedent(
            cls.description + '\n' +
            "type 'abkhazia prepare <corpus> --help' for help " +
            'on a specific corpus\n\n')

        subparsers = parser.add_subparsers(
            metavar='<corpus>', dest='corpus',
            help=textwrap.dedent('supported corpora are:\n' +
                                 '\n'.join(cls.describe_corpora())))

        for factory in cls.supported_corpora.itervalues():
            factory.add_parser(subparsers)

    @classmethod
    def run(cls, args):
        cls.supported_corpora[args.corpus].run(args)
