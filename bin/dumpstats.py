#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Parse the logs generated by PerformanceEvaluation for the collected metrics.
# Summarize the metrics using pandas, and produce a file containing summary
# statistics.
#
# Looks for log archives in under the path specified by $LOGS_HOME, or pwd, or
# at the path explicitly provided.
#
# The intended entry point is via Fabric task invocation, ie,
#   $ ~/tmp/fab/bin/fab -H localhost -f dumpstats.py dumpstats
# or
#   $ ~/tmp/fab/bin/fab -H localhost -f dumpstats.py dumpstats:/path/to/bucket-offheap-60g-30.tar.gz
#

from __future__ import with_statement
from fabric.api import *
from os import environ, getcwd
from os.path import basename, dirname, exists, splitext
from tempfile import mkstemp
import uuid
import pandas as pd
import numpy as np
import itertools as it
import sys

logs_home = environ.get('LOGS_HOME', getcwd())

@task
def summarize(arg):
    def writeln(f, s):
        f.write('%s\n' % s)

    df = None
    with open(arg, 'r') as f:
        df = pd.DataFrame(sorted(it.chain(*[eval(x) for x in f.read().strip().split('\n') if x])))
    with open('%s-summary.txt' % arg, 'w') as f:
        writeln(f, repr(df.describe()))     # 25, 50, 75 percentiles
        writeln(f, repr(df.describe(90)))   # 95 percentile
        writeln(f, repr(df.describe(98)))   # 99 percentile
        writeln(f, repr(df.describe(99.8))) # 99.9 percentile

@task
def dumpstats(f=None):
    if f:
        f = [f]
    else:
        f = run("find %s -iname '*tar.gz'" % logs_home).split()
    for tgz in f:
        print tgz
        conf = splitext(splitext(basename(tgz))[0])[0]
        print conf
        tmp_dir = '/tmp/%s' % uuid.uuid4()
        data_file = '%s/%s.txt' % (logs_home,conf)
        stats_file = '%s/%s-stats.txt' % (logs_home,conf)
        run('mkdir %s' % tmp_dir)
        with cd(tmp_dir):
            run('tar xvzf %s' % tgz)
            run("grep 'randomRead latency log (ms)' *.2.txt | cut -d: -f 5- > data.2.txt")
        run('cp %s/data.2.txt %s' % (tmp_dir,data_file))
        run('rm -rf %s' % tmp_dir)
        summarize(data_file)

