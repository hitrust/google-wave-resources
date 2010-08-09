# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__authors__ = ['christian.plesner.hansen@gmail.com (Christian Plesner Hansen)']

import traverse

class TestElement(object):

  def __init__(self, elm, start, end):
    self.elm_ = elm
    self.start_ = start
    self.end_ = end

  def start(self):
    return self.start_

  def end(self):
    return self.end_

  def enclose_in_ranges(self):
    return True

  def indent(self):
    return int(self.elm_[1])

  def range_type(self):
    return self.elm_[0]

  def __str__(self):
    return "%s@%i" % (str(self.range_type()), self.indent())


class TestBlip(object):

  def __init__(self, elements):
    self.elements_ = elements

  def elements(self):
    return self.elements_

  def length(self):
    return len(self.elements()) * 2

  def substring(self, start, end):
    return ""


class ExtractingVisitor(traverse.HtmlVisitor):

  def __init__(self):
    self.result_ = []

  def on_element_range_start(self, type, indent):
    self.result_.append("<%s-%i" % (type, indent))

  def on_element_range_end(self, type, indent):
    self.result_.append("%s-%i>" % (type, indent))

  def on_element_start(self, element):
    self.result_.append("{%s" % element.range_type())

  def on_element_end(self, element):
    self.result_.append("%s}" % element.range_type())


def test_element(input, expected):
  i = 0
  elms = []
  for e in input.split(' '):
    elms.append(TestElement(e.split(':'), i, i + 1))
    i += 2
  blip = TestBlip(elms)
  disp = traverse.HtmlVisitorDispatcher(blip)
  visitor = ExtractingVisitor()
  disp.dispatch(visitor)
  stream = " ".join(visitor.result_)
  print stream
  assert stream == expected


def test_elements():
  test_element('x:0 x:0', '<x-0 {x x} {x x} x-0>')
  test_element('x:0 x:1 x:0', '<x-0 {x x} <x-1 {x x} x-1> {x x} x-0>')
  test_element('x:2', '<x-0 <x-1 <x-2 {x x} x-2> x-1> x-0>')
  test_element('x:1 y:1 x:1', '<x-0 <x-1 {x x} x-1> <y-1 {y y} y-1> <x-1 {x x} x-1> x-0>')


def test():
  test_elements()


if __name__ == '__main__':
  test()
