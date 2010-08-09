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

class Event(object):

  END = -1
  START = 1

  def __init__(self, start, end, id):
    assert start <= end
    self.start_ = start
    self.end_ = end
    self.id_ = id

  def primary(self):
    if self.order() == Event.END:
      return self.end_
    else:
      return self.start_
  
  def secondary(self):
    if self.order() == Event.END:
      return self.start_
    else:
      return self.end_
  
  def skip_contents(self):
    return False

  # Comparison function that sorts range start and endpoints so that there is an
  # increasing order of start offsets of start points and end offsets of end
  # points.  Points at the same offset are ordered so end points come before 
  # start points, start points with closer end points come after start points 
  # with farther end points, and correspondingly for end points.  The id is used
  # as a tie breaker and ordered in increasing order for start points and
  # decreasing for end points.
  def __cmp__(self, other):
    primary_diff = self.primary() - other.primary()
    if primary_diff != 0:
      return primary_diff
    order_diff = self.order() - other.order()
    if order_diff != 0:
      return order_diff
    secondary_diff = other.secondary() - self.secondary()
    if secondary_diff != 0:
      return secondary_diff
    return self.order() * (other.id_ - self.id_)      


class StartElementRange(Event):

  def __init__(self, type, indent, start, end, id):
    super(StartElementRange, self).__init__(start, end, id)
    self.type_ = type
    self.indent_ = indent

  def dispatch(self, dispatcher, visitor):
    dispatcher.with_empty_annotation_stack(self.fire_raw_event, visitor)
  
  def fire_raw_event(self, visitor):
    visitor.on_element_range_start(self.type_, self.indent_)

  def order(self):
    return Event.START

  def __str__(self):
    return "start range %i [%i .. %i]" % (self.id_, self.start_, self.end_)


class EndElementRange(Event):

  def __init__(self, type, indent, start, end, id):
    super(EndElementRange, self).__init__(start, end, id)
    self.type_ = type
    self.indent_ = indent

  def dispatch(self, dispatcher, visitor):
    dispatcher.with_empty_annotation_stack(self.fire_raw_event, visitor)

  def fire_raw_event(self, visitor):
    visitor.on_element_range_end(self.type_, self.indent_)

  def order(self):
    return Event.END

  def __str__(self):
    return "end range %i [%i .. %i]" % (self.id_, self.start_, self.end_)


class OnElementStart(Event):

  def __init__(self, element, start, end, id):
    super(OnElementStart, self).__init__(start, end, id)
    self.element_ = element

  def dispatch(self, dispatcher, visitor):
    dispatcher.with_empty_annotation_stack(self.fire_raw_event, visitor)

  def fire_raw_event(self, visitor):
    visitor.on_element_start(self.element_)

  def order(self):
    return Event.START

  def __str__(self):
    return "start element %i [%i .. %i]" % (self.id_, self.start_, self.end_)


class OnElementEnd(Event):

  def __init__(self, element, start, end, id):
    super(OnElementEnd, self).__init__(start, end, id)
    self.element_ = element

  def dispatch(self, dispatcher, visitor):
    dispatcher.with_empty_annotation_stack(self.fire_raw_event, visitor)

  def fire_raw_event(self, visitor):
    visitor.on_element_end(self.element_)

  def order(self):
    return Event.END

  def __str__(self):
    return "end element %i [%i .. %i]" % (self.id_, self.start_, self.end_)


class OnAnnotationStart(Event):

  def __init__(self, annotation, start, end, id):
    super(OnAnnotationStart, self).__init__(start, end, id)
    self.annotation_ = annotation

  def dispatch(self, dispatcher, visitor):
    dispatcher.push_annotation(self.annotation_, visitor)

  def order(self):
    return Event.START


class OnAnnotationEnd(Event):

  def __init__(self, annotation, start, end, id):
    super(OnAnnotationEnd, self).__init__(start, end, id)
    self.annotation_ = annotation

  def dispatch(self, dispatcher, visitor):
    dispatcher.pop_annotation(self.annotation_, visitor)

  def order(self):
    return Event.END


class HtmlVisitor(object):

  # A range of the same type of elements with the same indentation is about to
  # start.  Note that the length of the "range" may actually be 1.
  def on_element_range_start(self, type, indent):
    pass
  
  # A range of the same type of elements with the same indentation is over.
  def on_element_range_end(self, type, indent):
    pass
  
  # An element is about to start.
  def on_element_start(self, element):
    pass

  # An element is over.
  def on_element_end(self, element):
    pass

  # An annotation is about to start.  Note that this event may be fired a number
  # of times for the same event since we may have to start and stop the
  # annotation to get proper nesting and the visitor will be notified each time.
  def on_annotation_start(self, annotation):
    pass

  # An annotation has ended.  Note that this event may be fired a number of
  # times for the same event since we may have to start and stop the annotation
  # to get proper nesting and the visitor will be notified each time.  
  def on_annotation_end(self, annotation):
    pass

  def on_text(self, text):
    pass


class HtmlVisitorDispatcher(object):
  
  def __init__(self, blip):
    self.range_stack_ = []
    self.annot_stack_ = []
    self.events_ = []
    self.next_id_ = 0
    self.blip_ = blip

  # Generates a new unique integer id.  Ids are used as a tie breaker when
  # sorting annotations and elements.
  def gen_id(self):
    result = self.next_id_
    self.next_id_ += 1
    return result

  # Adds events corresponding to all annotations
  def add_annotation_events(self):
    for annot in self.blip_.annotations():
      id = self.gen_id()
      start = annot.start()
      end = annot.end()
      self.events_.append(OnAnnotationStart(annot, start, end, id))
      self.events_.append(OnAnnotationEnd(annot, start, end, id))

  # Pops the annotation stack empty, invokes the thunk, and pushes the
  # annotations back on again, notifying the visitor throughout.
  def with_empty_annotation_stack(self, thunk, visitor):
    if len(self.annot_stack_) == 0:
      thunk(visitor)
    else:
      top = self.annot_stack_.pop()
      visitor.on_annotation_end(top)
      self.with_empty_annotation_stack(thunk, visitor)
      visitor.on_annotation_start(top)
      self.annot_stack_.append(top)
  
  # Pushes the specified annotation, notifying the visitor
  def push_annotation(self, annotation, visitor):
    self.annot_stack_.append(annotation)
    visitor.on_annotation_start(annotation)
  
  # Pops the specified annotation, notifying the visitor.  Note that annotations
  # don't properly nest so this may require other annotations to be popped off
  # to reach the desired annotation and then on again, of which the visitor will
  # also be notified.
  def pop_annotation(self, annotation, visitor):
    popped = self.annot_stack_.pop()
    visitor.on_annotation_end(popped)
    if popped != annotation:
      self.pop_annotation(annotation, visitor)
      self.annot_stack_.append(popped)
      visitor.on_annotation_start(popped)

  # Process all elements and add associated events to the event
  # stream.  Series of elements for whom enclose_in_ranges() returns True are
  # enclosed in StartElementRange and EndElementRange events so that before any
  # such element with indent K there will be K+1 BeginLineRange elements, the
  # K+1'th of which will have the same range_type as the element.  Series of N
  # such elements with the same range_type and indent will only be enclosed in
  # one Start/EndElementRange pair.
  def add_element_events(self):
    last_end = 0
    for element in self.blip_.elements():
      start = element.start()
      end = element.end()
      self.update_ranges(element, start)
      id = self.gen_id()
      self.events_.append(OnElementStart(element, start, end, id))
      self.events_.append(OnElementEnd(element, start, end, id))
      last_end = end
    self.pop_range_stack_to(0, self.blip_.length())

  # Emit the Begin/End events to make the range state consistent with the
  # contract of build_element_events.
  def update_ranges(self, element, current_pos):
    # If this element doesn't use ranges we just close all open ranges.
    if not element.enclose_in_ranges():
      self.pop_range_stack_to(0, current_pos)
      return
    indent = element.indent() + 1
    range_type = element.range_type()
    # Close ranges until the nesting is no higher than the required indentation
    self.pop_range_stack_to(indent, current_pos)
    # If the nearest Start event doesn't match the present one we close that too
    if (len(self.range_stack_) == indent) and (self.range_stack_[-1][0] != range_type):
      self.pop_range_stack_to(indent - 1, current_pos)
    # And then we emit Start events to match the required indentation
    self.push_range_stack_to(indent, range_type, element)

  # Close open ranges until at most 'level' ranges are open.
  def pop_range_stack_to(self, level, current_pos):
    while len(self.range_stack_) > level:
      id = self.gen_id()
      (type, start) = self.range_stack_.pop()
      indent = len(self.range_stack_)
      start_event = StartElementRange(type, indent, start, current_pos, id)
      self.events_.append(start_event)
      end_event = EndElementRange(type, indent, start, current_pos, id)
      self.events_.append(end_event)

  # Start ranges of type 'type' until there's 'level' open ranges.   
  def push_range_stack_to(self, level, type, element):
    start = element.start()
    while len(self.range_stack_) < level:
      self.range_stack_.append((type, start))

  # Process the blip structure and deliver the appropriate events to the
  # visitor.
  def dispatch(self, visitor):
    self.add_element_events()
    self.add_annotation_events()
    self.events_.sort()
    self.fire_events(visitor)
  
  def fire_events(self, visitor):
    last_text_pos = 0
    for event in self.events_:
      primary = event.primary()
      if last_text_pos < primary:
        chunk = self.blip_.substring(last_text_pos, primary)
        visitor.on_text(chunk)
        last_text_pos = primary
      if (event.order() == Event.START) and (event.skip_contents()):
        last_text_pos = event.end()
      event.dispatch(self, visitor)
    if last_text_pos < self.blip_.length():
      visitor.on_text(self.blip_.substring(last_text_pos, self.blip_.length()))
