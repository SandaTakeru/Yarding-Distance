# -*- coding: utf-8 -*-

__author__ = 'Sanda takeru / HOKKAIDO Regional Forest Office'
__date__ = '2024-05-20'
__copyright__ = '(C) 2024 by Sanda takeru / HOKKAIDO Regional Forest Office'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import sys
import inspect

from qgis.core import QgsApplication
from .yarding_distance_provider import YardingDistanceProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class YardingDistancePlugin(object):

    def __init__(self):
        self.provider = None

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = YardingDistanceProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
