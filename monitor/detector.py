"""
This is my code for learning what normal looks like on a specific
machine, then watching for readings that fall outside that normal
range.

I built two modes into this. In learning mode, my program keeps
adjusting its own sense of what normal looks like. In watching mode,
it holds that sense steady and speaks up when something looks off.

I am using a small piece from the River library that is built to
look at one reading at a time, without needing to start over from
scratch, which makes it light enough to run on a Raspberry Pi.
"""

from river import anomaly
import storage

# I use one watcher per metric, since memory acting up and disk
# acting up are two different kinds of problems
METRICS = ["cpu_percent", "memory_percent", "disk_percent", "temperature_c"]

# the normal range I expect for each metric, so the watcher knows how
# to scale things. percents naturally run from 0 to 100, and I gave
# temperature a wide range since machines vary a lot
METRIC_LIMITS = {
    "cpu_percent": (0, 100),
    "memory_percent": (0, 100),
    "disk_percent": (0, 100),
    "temperature_c": (0, 110),
}

# how unusual a reading needs to look before I call it a problem
# the number I compare against runs from 0 to 1, closer to 1 means
# more unusual
ANOMALY_THRESHOLD = 0.9

# how genuinely high a reading has to be in plain terms before I will
# even consider calling it a problem, no matter how unusual it looks
# compared to what I have learned. this stops a quiet warm up period
# from making ordinary computer use look like an emergency
METRIC_FLOORS = {
    "cpu_percent": 70,
    "memory_percent": 85,
    "disk_percent": 90,
    "temperature_c": 75,
}

# how many readings I collect before I start trusting what the
# watcher flags. it looks back over its most recent 250 readings, so
# I want at least that many before its sense of normal has settled
MIN_READINGS_BEFORE_FLAGGING = 250


def _new_watcher(metric):
    return anomaly.HalfSpaceTrees(seed=42, limits={metric: METRIC_LIMITS[metric]})


class Detector:
    def __init__(self):
        self.watchers = {m: _new_watcher(m) for m in METRICS}
        # I start this at zero every time the program starts, since
        # what I have actually learned also starts at zero every
        # time. Keeping these two in sync is what makes the warm up
        # time mean anything.
        self.reading_count = 0
        storage.set_state("reading_count", self.reading_count)

    def process(self, reading):
        """
        I feed one reading into each watcher and return a list of
        anything unusual I found. Each watcher looks at the reading
        and also learns from it at the same time.

        I keep it always learning on purpose, even from things it
        just flagged. If I stopped it from learning the moment it
        got something wrong, one bad guess could lock it into being
        wrong forever, with no way to correct itself. Always learning
        does mean a real problem can eventually stop looking unusual
        if it keeps happening again and again, but that matches how
        I already designed the rest of this, if the machine's normal
        pattern genuinely changes, I switch it back to learning mode
        on purpose to let it catch up.
        """
        mode = storage.get_state("mode", "learning")
        self.reading_count += 1
        storage.set_state("reading_count", self.reading_count)

        found = []
        for metric in METRICS:
            value = reading.get(metric)
            if value is None:
                continue

            watcher = self.watchers[metric]
            x = {metric: value}

            unusualness = watcher.score_one(x)
            watcher.learn_one(x)

            still_warming_up = self.reading_count < MIN_READINGS_BEFORE_FLAGGING
            looks_unusual = unusualness >= ANOMALY_THRESHOLD
            is_genuinely_high = value >= METRIC_FLOORS[metric]

            if mode == "watching" and not still_warming_up and looks_unusual and is_genuinely_high:
                severity = "high" if unusualness >= 0.9 else "medium"
                found.append({"metric": metric, "value": value, "severity": severity, "score": unusualness})

        return found


if __name__ == "__main__":
    # a quick check I run by hand, with made up numbers, normal
    # readings around 20, then one reading way out of range, just to
    # confirm my program actually catches it
    storage.init_db()
    storage.set_state("mode", "watching")
    d = Detector()
    d.reading_count = MIN_READINGS_BEFORE_FLAGGING  # I skip the warm up time for this check

    import random
    false_alarms = 0
    for i in range(300):
        fake = {"cpu_percent": 20 + random.uniform(-2, 2), "memory_percent": 40, "disk_percent": 50, "temperature_c": 45}
        result = d.process(fake)
        if result:
            false_alarms += 1
    print(f"false alarms on normal data: {false_alarms} out of 300")

    fake_spike = {"cpu_percent": 99, "memory_percent": 40, "disk_percent": 50, "temperature_c": 45}
    result = d.process(fake_spike)
    print("result on the made up spike:", result)

    # the real check, does a repeated spike keep getting caught, or
    # does it quietly stop being flagged the more it happens
    caught_count = 0
    for i in range(20):
        result = d.process(fake_spike)
        if result:
            caught_count += 1
    print(f"caught {caught_count} out of 20 repeated spikes")