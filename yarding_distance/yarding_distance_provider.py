# -*- coding: utf-8 -*-

__author__ = 'Sanda takeru'
__date__ = '2024-05-20'
__copyright__ = '(C) 2024 by Sanda takeru'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from pathlib import Path

from PyQt5.QtGui import QIcon
from qgis.core import QgsProcessingProvider
from .yarding_distance_algorithm import create_algorithms


class YardingDistanceProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        for alg in create_algorithms():
            self.addAlgorithm(alg)
    
    def id(self):
        return 'Yarding Distance'

    def name(self):
        return self.tr('Yarding Distance 平均集材距離')

    def icon(self):
        path = (Path(__file__).parent / "icon.svg").resolve()
        return QIcon(str(path))

    def longName(self):
        return self.name()
