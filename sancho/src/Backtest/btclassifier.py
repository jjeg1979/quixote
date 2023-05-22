from pathlib import Path
from pyBTAnalyst.src.btparser import METATRADER4, GENBOX

import pandas as pd


class Btclassifier:
    def __init__(self, path: Path, bts: list) -> None:
        self._path = path
        self._bts = bts

    @property
    def path(self) -> Path:
        return Path(self._path)

    @path.setter
    def path(self, value: Path):
        self._path = value if value is Path else ValueError

    @property
    def bts(self) -> dict:
        return self._bts if (self._bts is not None and len(self._bts) >= 1) else {}

    @bts.setter
    def bts(self, value: list) -> None:
        self._bts = value if value is list else TypeError

    def classification(self) -> dict:
        return {bt: METATRADER4 if len(pd.read_html(self._path/Path(bt))) == 2 else
        GENBOX for bt in self.bts}
