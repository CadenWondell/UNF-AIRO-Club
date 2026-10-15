"""V-14 probe: does CalibratedClassifierCV(cv=GroupKFold) receive `groups` during fit?"""

import sys
import warnings

import numpy as np
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold


class SpyGroupKFold(GroupKFold):
    seen = []

    def split(self, X, y=None, groups=None):
        SpyGroupKFold.seen.append(groups is not None)
        return super().split(X, y, groups)


rng = np.random.default_rng(0)
X = rng.normal(size=(200, 3))
y = (X[:, 0] + rng.normal(size=200) > 0).astype(int)
groups = np.repeat(np.arange(50), 4)
print("python", sys.version.split()[0], "sklearn", sklearn.__version__)
for routing in (False, True):
    SpyGroupKFold.seen = []
    try:
        if routing:
            sklearn.set_config(enable_metadata_routing=True)
            est = (
                LogisticRegression().set_fit_request(sample_weight=False)
                if hasattr(LogisticRegression(), "set_fit_request")
                else LogisticRegression()
            )
        else:
            sklearn.set_config(enable_metadata_routing=False)
            est = LogisticRegression()
        cal = CalibratedClassifierCV(est, cv=SpyGroupKFold(n_splits=5), method="sigmoid")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cal.fit(X, y, groups=groups)
        print(f"routing={routing}: fit OK; splitter received groups: {SpyGroupKFold.seen}")
    except Exception as e:
        print(f"routing={routing}: {type(e).__name__}: {str(e)[:160]}")
    finally:
        sklearn.set_config(enable_metadata_routing=False)
