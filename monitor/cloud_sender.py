"""
This is the piece that sends my findings out to the small online
service. If the connection is down when something is found, I save
it and try again later, so nothing gets lost over a short outage.
"""

import json
import urllib.request
import urllib.error

import storage

# Replace this with the URL of your deployed Cloudflare Worker.
WORKER_URL = "https://YOUR_WORKER_NAME.YOUR_ACCOUNT_NAME.workers.dev/report-anomaly"


def send_anomaly(anomaly):
    body = json.dumps({
        "metric": anomaly["metric"],
        "value": anomaly["value"],
        "severity": anomaly["severity"],
        "timestamp": anomaly["timestamp"],
    }).encode("utf-8")

    request = urllib.request.Request(
        WORKER_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "kvm-monitor-local-agent/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            result = json.loads(response.read())
            return True, result
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {e.code}: {detail[:300]}"
    except (urllib.error.URLError, TimeoutError) as e:
        return False, str(e)


def flush_unsent():
    """
    I call this on a schedule. It looks for any findings that never
    made it out, tries to send them, and marks the ones that succeed
    so I do not send them twice.
    """
    unsent = storage.get_unsent_anomalies()
    if not unsent:
        return

    print(f"trying to send {len(unsent)} unsent finding(s) to {WORKER_URL}")

    for anomaly in unsent:
        ok, result = send_anomaly(anomaly)
        if ok:
            storage.mark_anomaly_sent(anomaly["id"])
            print(f"sent finding {anomaly['id']} successfully")
        else:
            # I print the real reason here so I am not left guessing
            print(f"could not send finding {anomaly['id']}: {result}")
            # I stop here for now, since if the connection is down,
            # the rest will likely fail too, and I will try again
            # next time this runs
            break