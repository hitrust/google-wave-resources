#!/usr/bin/python2.4
#
# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Defines classes that are needed to model a search (results)."""

import errors
import wavelet

class Results(object):
  """Models a set of search results.

  Search results are composed of a list of digests, query, and number of
  results.
  """

  def __init__(self, json):
    """Inits this results object with JSON data.

    Args:
      json: JSON data dictionary from Wave server.
    """
    self._query = json.get('query')
    self._num_results = json.get('numResults')
    self._digests = []
    for digest_data in json['digests']:
      digest = Digest(digest_data)
      self._digests.append(digest)


  @property
  def query(self):
    """Returns this wavelet's parent wave id."""
    return self._query

  @property
  def num_results(self):
    """Returns this wavelet's parent wave id."""
    return self._num_results

  @property
  def digests(self):
    """Returns this wavelet's parent wave id."""
    return self._digests

  def serialize(self):
    """Return a dict of the wavelet properties."""
    return {'query': self._query,
            'numResults': self._num_results,
           }


class Digest(object):
  """Models a single digest.

  A digest is composed of title, wave ID, snippet, and participants.
 """

  def __init__(self, json):
    """Inits this digest with JSON data.

    Args:
      json: JSON data dictionary from Wave server.
    """
    self._wave_id = json.get('waveId')
    self._title = json.get('title')
    self._snippet = json.get('snippet')
    self._participants = wavelet.Participants(json.get('participants', []),
                                      {},
                                      self._wave_id,
                                      '',
                                      None)
    self._raw_data = json

  @property
  def wave_id(self):
    """Returns this wavelet's parent wave id."""
    return self._wave_id

  @property
  def snippet(self):
    """Returns the snippet."""
    return self._snippet

  @property
  def domain(self):
    """Return the domain that wavelet belongs to."""
    p = self._wave_id.find('!')
    if p == -1:
      return None
    else:
      return self._wave_id[:p]

  @property
  def participants(self):
    """Returns a set of participants on this wavelet."""
    return self._participants

  @property
  def title(self):
    return self._title

  def serialize(self):
    """Return a dict of the wavelet properties."""
    return {'waveId': self._wave_id,
            'participants': self._participants.serialize(),
            'title': self._title,
            'snippet': self._snippet,
           }
