import gc
import array

class NoteTrack:
    __slots__ = ("times", "lanes", "specials", "lengths", "count")

    def __init__(self, times, lanes, specials, lengths, count):
        self.times = times
        self.lanes = lanes
        self.specials = specials
        self.lengths = lengths
        self.count = count

    def __len__(self):
        return self.count

    def __getitem__(self, i):
        return (self.times[i], self.lanes[i], bool(self.specials[i]), self.lengths[i])

    def __iter__(self):
        for i in range(self.count):
            yield (self.times[i], self.lanes[i], bool(self.specials[i]), self.lengths[i])


class SongLoader:
    def __init__(self, chart_path):
        self.chart_path = chart_path

    def load_chart(self, difficulty="ExpertSingle"):
        gc.collect()

        resolution = 192  
        bpm_ticks = array.array('I')
        bpm_values = array.array('f')

        try:
            with open(self.chart_path, "r") as f:
                current_section = None
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        current_section = line[1:-1]
                        continue
                    if "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip()

                    if current_section == "Song" and key == "Resolution":
                        try:
                            resolution = int(val)
                        except ValueError:
                            pass
                    elif current_section == "SyncTrack" and key.isdigit():
                        parts = val.split()
                        if len(parts) >= 2 and parts[0] == "B":
                            bpm_ticks.append(int(key))
                            bpm_values.append(int(parts[1]) / 1000.0)
        except OSError:
            return None

        if len(bpm_ticks) == 0:
            bpm_ticks.append(0)
            bpm_values.append(120.0)

        gc.collect()

        note_count = 0
        sp_starts = array.array('I')
        sp_ends = array.array('I')

        try:
            with open(self.chart_path, "r") as f:
                in_target = False
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        section = line[1:-1]
                        if section == difficulty:
                            in_target = True
                        else:
                            if in_target: break
                            in_target = False
                        continue
                    if not (in_target and "=" in line):
                        continue
                    
                    key, _, val = line.partition("=")
                    if not key.strip().isdigit():
                        continue

                    tick = int(key.strip())
                    parts = val.strip().split()
                    if len(parts) < 2:
                        continue

                    if parts[0] == "N":
                        note_count += 1
                    elif parts[0] == "S" and parts[1] == "2" and len(parts) >= 3:
                        length = int(parts[2])
                        sp_starts.append(tick)
                        sp_ends.append(tick + length)
        except OSError:
            return None

        if note_count == 0:
            return None

        times = array.array('I', bytes(4 * note_count))
        lengths = array.array('I', bytes(4 * note_count)) # Guarda o tamanho
        lanes = array.array('B', bytes(note_count))
        specials = array.array('B', bytes(note_count))

        gc.collect()

        idx = 0
        bpm_idx = 0
        current_bpm = bpm_values[0]
        last_tick = 0
        ms_accum = 0.0
        sp_idx = 0
        num_phrases = len(sp_starts)

        try:
            with open(self.chart_path, "r") as f:
                in_target = False
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        section = line[1:-1]
                        if section == difficulty:
                            in_target = True
                        else:
                            if in_target: break
                            in_target = False
                        continue
                    if not (in_target and "=" in line):
                        continue

                    key, _, val = line.partition("=")
                    if not key.strip().isdigit():
                        continue

                    tick = int(key.strip())
                    parts = val.strip().split()
                    if len(parts) < 2 or parts[0] != "N":
                        continue

                    lane = int(parts[1])
                    if not (0 <= lane <= 4):
                        continue

                    # Calcula a duração da nota (se for segurada)
                    note_len_ticks = int(parts[2]) if len(parts) >= 3 else 0

                    while bpm_idx + 1 < len(bpm_ticks) and bpm_ticks[bpm_idx + 1] <= tick:
                        next_tick = bpm_ticks[bpm_idx + 1]
                        ms_accum += ((next_tick - last_tick) / resolution) * (60000.0 / current_bpm)
                        last_tick = next_tick
                        current_bpm = bpm_values[bpm_idx + 1]
                        bpm_idx += 1

                    note_ms = ms_accum + ((tick - last_tick) / resolution) * (60000.0 / current_bpm)
                    note_len_ms = (note_len_ticks / resolution) * (60000.0 / current_bpm)

                    while sp_idx < num_phrases and sp_ends[sp_idx] < tick:
                        sp_idx += 1
                    is_special = sp_idx < num_phrases and sp_starts[sp_idx] <= tick <= sp_ends[sp_idx]

                    if idx < note_count:
                        times[idx] = int(note_ms)
                        lengths[idx] = int(note_len_ms)
                        lanes[idx] = lane
                        specials[idx] = 1 if is_special else 0
                        idx += 1
        except OSError:
            return None

        gc.collect()
        return NoteTrack(times, lanes, specials, lengths, idx)