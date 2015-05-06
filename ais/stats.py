#!/usr/bin/env python

import argparse
import collections
import logging
import pprint
import sys

from ais import nmea_queue


class TrackRange(object):

  def __init__(self):
    self.min = None
    self.max = None

  def AddValues(self, *values):
    print ('AddValues', values)
    if not len(values):
      raise ValueError('Must specify at least 1 value.')
    if self.min is None:
      self.min = min(values)
      self.max = max(values)
      return
    self.min = min(self.min, *values)
    self.max = max(self.max, *values)


class Stats(object):

  def __init__(self):
    self.counts = collections.Counter()
    self.queue = nmea_queue.NmeaQueue()
    self.time_range = TrackRange()
    self.time_delta_range = TrackRange()

  def AddFile(self, iterable, filename=None):
    self.counts['files'] += 1

    for line in iterable:
      self.AddLine(line)

  def AddLine(self, line):
    self.counts['lines'] += 1
    self.queue.put(line)
    msg = self.queue.GetOrNone()
    if not msg:
      return

    # logging.info('stats found msg: %s', msg)
    print ()
    pprint.pprint(msg)
    self.counts[msg['line_type']] += 1
    if 'decoded' in msg:
      decoded = msg['decoded']
      if 'id' in decoded:
        self.counts['msg_VDM_%s' % decoded['id']] += 1
      if 'msg' in decoded:
        self.counts['msg_%s' % decoded['msg']] += 1

    if 'times' in msg:
      if self.time_range.min is None:
        self.time_range.AddValues(*msg['times'])
        # self.time_delta_range.AddValues(msg['times'])
      else:
        print (self.time_range.min, self.time_range.max)
        time_delta = max(msg['times']) - self.time_range.max
        self.time_delta_range.AddValues(time_delta)
        self.time_range.AddValues(*msg['times'])


  def PrintSummary(self):
    pprint.pprint(self.counts)
    logging.info('time_range: %s to %s',
                 self.time_range.min,
                 self.time_range.max)
    logging.info('time_delta_range: %s to %s',
                 self.time_delta_range.min,
                 self.time_delta_range.max)



def main():
  logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  # logger = logging.getLogger('fiona.tool')
  logging.info('in main')

  parser = argparse.ArgumentParser()
  parser.add_argument('filenames', type=str, nargs='+', help='NMEA files')
  args = parser.parse_args()
  logging.info('args: %s', args)

  stats = Stats()
  for filename in args.filenames:
      stats.AddFile(open(filename), filename)

  stats.PrintSummary()

