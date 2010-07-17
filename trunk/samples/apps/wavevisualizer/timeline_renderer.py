import logging
from datetime import date


def render_wavelet(wavelet):
  blips = []
  for blip_id in wavelet.blips:
    blip = wavelet.blips.get(blip_id)
    # find modified time of blip
    blips.append(blip)

  # sort by modified time
  blips_by_time = sorted(blips, key=lambda blip: blip.last_modified_time)

  data_rows = []
  num_in_day = 0
  total = 0
  old_time = None
  # create a list where each entry represents 1 day of blips
  for blip in blips_by_time:
    time = date.fromtimestamp(blip.last_modified_time/1000)
    if old_time:
      time_diff = abs(time - old_time)
    if old_time and time_diff.days > 0:
      # put old time info in array
      # reset num counter
      data = {'year': old_time.year,
            'month': old_time.month,
            'day': old_time.day,
            'total': total}
      num_in_day = 0
      data_rows.append(data)
    num_in_day += 1
    total += 1
    old_time = time


  data = {'year': old_time.year,
            'month': old_time.month,
            'day': old_time.day,
            'total': total}
  data_rows.append(data)

  # iterate through, check if new day found, put in new day bucket
  return data_rows
