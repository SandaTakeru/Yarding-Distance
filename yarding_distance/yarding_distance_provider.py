# -*- coding: utf-8 -*-

__author__ = 'Sanda takeru'
__date__ = '2024-05-20'
__copyright__ = '(C) 2024 by Sanda takeru'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from pathlib import Path

from PyQt5.QtGui import QIcon
from qgis.core import QgsProcessingProvider
from .yarding_distance_algorithm import YardingDistanceSingleClickManhattan, YardingDistanceSingleClickEuclid, YardingDistancePointLayerManhattan, YardingDistancePointLayerEuclid


class YardingDistanceProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(YardingDistanceSingleClickManhattan())
        self.addAlgorithm(YardingDistanceSingleClickEuclid())
        self.addAlgorithm(YardingDistancePointLayerManhattan())
        self.addAlgorithm(YardingDistancePointLayerEuclid())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self):
        return 'Yarding Distance'

    def name(self):
        return self.tr('Yarding Distance 平均集材距離')

    def icon(self):
        path = (Path(__file__).parent / "icon.svg").resolve()
        return QIcon(str(path))

    def longName(self):
        return self.name()
