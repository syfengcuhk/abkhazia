#!/bin/bash
# Copyright 2015, 2016 Thomas Schatz, Xuan Nga Cao, Mathieu Bernard
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
# along with abkahzia. If not, see <http://www.gnu.org/licenses/>.


# This exemple script computes force alignment of a subsample of the
# buckeye corpus. This exemple relies on tiny data and should be run
# locally. Writes to $data_dir, the final alignment will be in the
# $data_dir/split/train/align/export directory.

data_dir=${1:-/home/mbernard/data/abkhazia/exemple}
data_dir=$(readlink -f $data_dir)
#rm -rf $data_dir
mkdir -p $data_dir

# prepare the corpus. Here we assume you have a raw buckeye
# distribution and the 'buckeye-directory' is set in the abkhazia
# configuration file.
abkhazia prepare buckeye -o $data_dir || exit 1

# split the prepared corpus in train and test sets. We keep only 5%
# for training and split by utterances (this is an exemple, in real
# life consider taking more than 5% of the data).
abkhazia split $data_dir -T 0.05 || exit 1
train_dir=$data_dir/split/train

# compute a language model on the train set
abkhazia language $train_dir -l word -n 3 || exit 1

# compute MFCC features
abkhazia features $train_dir || exit 1

# The test.cfg file comes with very small parameters for triphone
# modeling, this reduce computation time (no matter the model quality).
abkhazia -c ../test/test.cfg acoustic $train_dir -t tri || exit 1

# compute forced-alignment from 3-gram and triphone model
abkhazia align $train_dir || exit 1

echo "symlink the result to $data_dir/forced_alignment.txt"
ln -s -f $train_dir/align/export/forced_alignment.txt $data_dir