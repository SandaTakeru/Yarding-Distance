# -*- coding: utf-8 -*-

__author__ = 'Sanda takeru / HOKKAIDO Regional Forest Office'
__date__ = '2024-05-20'
__copyright__ = '(C) 2024 by Sanda takeru / HOKKAIDO Regional Forest Office'

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load YardingDistance class from file YardingDistance.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .yarding_distance import YardingDistancePlugin
    return YardingDistancePlugin()
