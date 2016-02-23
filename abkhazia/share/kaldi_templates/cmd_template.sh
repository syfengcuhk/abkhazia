# "queue.pl" uses qsub.  The options to it are
# options to qsub.  If you have GridEngine installed,
# change this to a queue you have access to.
# Otherwise, use "run.pl", which will run jobs locally
# (make sure your --num-jobs options are no more than
# the number of cpus on your machine.

# On Oberon use:
# export train_cmd="queue.pl -q all.q@puck*.cm.cluster"
# export decode_cmd="queue.pl -q all.q@puck*.cm.cluster"
# export highmem_cmd="queue.pl -q all.q@puck*.cm.cluster"

# On Eddie use:
# export train_cmd="queue.pl -P inf_hcrc_cstr_general"
# export decode_cmd="queue.pl -P inf_hcrc_cstr_general"
# export highmem_cmd="queue.pl -P inf_hcrc_cstr_general -pe memory-2G 2"

# To run locally, use:
export train_cmd=run.pl
export decode_cmd=run.pl
export highmem_cmd=run.pl
