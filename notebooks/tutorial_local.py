import datetime
import sys
import threading

import datajoint as dj
import matplotlib.pyplot as plt
import numpy as np
import suite2p

from tests.tutorial_pipeline import (
    Equipment,
    imaging,
    imaging_report,
    lab,
    scan,
    session,
    subject,
)

sys.path.append("/element-calcium-imaging")

dj.config["database.host"] = "localhost"
dj.config["database.user"] = "root"
dj.config["database.password"] = "simple"
dj.config["custom"] = {
    "imaging_root_data_dir": "/element-calcium-imaging/data",
    "database_prefix": "root_",
}
dj.config.save_local()
dj.conn()

(
    dj.Diagram(subject.Subject)
    + dj.Diagram(session.Session)
    + dj.Diagram(scan)
    + dj.Diagram(imaging)
)

subject.Subject.insert1(
    dict(
        subject="TG6s-001",
        subject_nickname="Jin",
        sex="M",
        subject_birth_date="2022-09-07",
        subject_description="ScanImage acquisition. Suite2p processing.",
    ),
    skip_duplicates=True,
)

session_key = dict(subject="TG6s-001", session_datetime="2022-11-15 16:50:20")
session.Session.insert1(session_key, skip_duplicates=True)
session.SessionDirectory.insert1(
    dict(**session_key, session_dir="TG6s-001/accel001"), skip_duplicates=True
)

Equipment.insert1(
    dict(
        device="Nikon A1",
        modality="Calcium imaging",
        description="Nikon A1 2 photon microscope",
    ),
    skip_duplicates=True,
)
scan.Scan.insert1(
    dict(
        **session_key,
        scan_id=0,
        device="Nikon A1",
        acq_software="NIS",  # 実在のソフトしか選べない
        scan_notes="",
    ),
    skip_duplicates=True,
)
scan.ScanInfo.populate(display_progress=True)

params_suite2p = suite2p.default_ops()
params_suite2p["nonrigid"] = False
params_suite2p["tau"] = 1.4
params_suite2p["fs"] = 30

imaging.ProcessingParamSet.insert_new_params(
    processing_method="suite2p",
    paramset_idx=0,
    params=params_suite2p,
    paramset_desc="Calcium imaging analysis with Suite2p using default parameters",
)
imaging.ProcessingTask.insert1(
    dict(
        **session_key,
        scan_id=0,
        paramset_idx=0,
        task_mode="load",  # load or trigger
        processing_output_dir="TG6s-001/accel001/suite2p",
    ),
    skip_duplicates=True,
)
imaging.Processing.populate(session_key, display_progress=True)

print(subject.Subject())
print(session.Session())
print(session.SessionDirectory())
print(scan.Scan())
print(scan.ScanInfo())

# imaging.Processing.populate(session_key, display_progress=True)
# imaging.MotionCorrection.populate(display_progress=True)
# imaging.Segmentation.populate(display_progress=True)
# imaging.Fluorescence.populate(display_progress=True)
# imaging.Activity.populate(display_progress=True)
# imaging_report.ScanLevelReport.populate(display_progress=True)
# imaging_report.TraceReport.populate(display_progress=True)

trace = (imaging.Fluorescence.Trace & "mask = '10'").fetch1("fluorescence")
sampling_rate = (scan.ScanInfo & session_key & "scan_id=0").fetch1("fps")

plt.plot(np.r_[: trace.size] * 1 / sampling_rate, trace)
plt.title("Fluorescence trace for mask 10")
plt.xlabel("Time (s)")
plt.ylabel("Activity (a.u.)")

# scan_key = (scan.Scan & "scan_id=0").fetch1("KEY")
# average_image = (imaging.MotionCorrection.Summary & scan_key & "field_idx=0").fetch1(
#     "average_image"
# )

# plt.imshow(average_image)
plt.show()
