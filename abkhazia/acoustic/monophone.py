# Copyright 2016 Thomas Schatz, Xuan-Nga Cao, Mathieu Bernard
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
"""Training monophone acoustic models"""

import os

import abkhazia.utils as utils
import abkhazia.features as features
from abkhazia.acoustic.abstract_acoustic_model import (
    AbstractAcousticModel)
import abkhazia.kaldi as kaldi


class Monophone(AbstractAcousticModel):
    """Wrapper on Kaldi egs/wsj/s5/steps/train_mono.sh

    Training is done on an abkhazia corpus, from computed features with cmvn.

    The following options are not forwarded from Kaldi to
    Abkhazia: power, cmvn_opts.

    """
    model_type = 'mono'

    options = {k: v for k, v in (
        kaldi.options.make_option(
            'transition-scale', default=1.0, type=float,
            help='Transition-probability scale (relative to acoustics)'),
        kaldi.options.make_option(
            'self-loop-scale', default=0.1, type=float,
            help=('Scale of self-loop versus non-self-loop log probs '
                  '(relative to acoustics)')),
        kaldi.options.make_option(
            'acoustic-scale', default=0.1, type=float,
            help='Scaling factor for acoustic likelihoods'),
        kaldi.options.make_option(
            'num-iterations', default=40, type=int,
            help='Number of iterations for training'),
        kaldi.options.make_option(
            'max-iteration-increase', default=30, type=int,
            help='Last iteration to increase number of Gaussians on'),
        kaldi.options.make_option(
            'total-gaussians', default=1000, type=int,
            help='Target number of Gaussians at the end of training'),
        kaldi.options.make_option(
            'careful', default=False, type=bool,
            help=('If true, do careful alignment, which is better at '
                  'detecting alignment failure (involves loop to start '
                  'of decoding graph)')),
        kaldi.options.make_option(
            'boost-silence', default=1.0, type=float,
            help=('Factor by which to boost silence likelihoods '
                  'in alignment')),
        kaldi.options.make_option(
            'realign-iterations', type=list,
            default=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12,
                     14, 16, 18, 20, 23, 26, 29, 32, 35, 38],
            help='Iterations on which to align features on the model'))}

    def __init__(self, corpus, feats_dir, output_dir, lang_args,
                 log=utils.logger.null_logger()):
        super(Monophone, self).__init__(
            corpus, feats_dir, output_dir, lang_args, log=log)

    def check_parameters(self):
        super(Monophone, self).check_parameters()

        # ensure cmvn are computed for the features
        features.Features.check_features(self.input_dir, cmvn=True)

    def run(self):
        self._train_mono()

    def _train_mono(self):
        # Flat start and monophone training, with delta-delta features.
        # This script applies cepstral mean normalization (per speaker).
        message = 'training monophone model'
        target = os.path.join(self.recipe_dir, 'exp', self.model_type)
        command = (
            'steps/train_mono.sh --nj {njobs} --cmd "{cmd}" '
            '--scale-opts "--transition-scale={transition} '
            '--acoustic-scale={acoustic} --self-loop-scale={selfloop}" '
            '--num-iters {niters} --max-iter-inc {maxinc} --totgauss {ngauss} '
            '--careful {careful} --boost-silence {boost} '
            '--realign-iters {realign} {data} {lang} {target}'
            .format(
                njobs=self.njobs,
                cmd=utils.config.get('kaldi', 'train-cmd'),
                transition=self._opt('transition-scale'),
                acoustic=self._opt('acoustic-scale'),
                selfloop=self._opt('self-loop-scale'),
                niters=self._opt('num-iterations'),
                maxinc=self._opt('max-iteration-increase'),
                ngauss=self._opt('total-gaussians'),
                careful=self._opt('careful'),
                boost=self._opt('boost-silence'),
                realign=self._opt('realign-iterations'),
                data=self.data_dir,
                lang=self.lang_dir,
                target=target))
        self._run_am_command(command, target, message)
