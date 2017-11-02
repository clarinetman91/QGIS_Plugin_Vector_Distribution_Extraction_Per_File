# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VectorDistributionExtractionPerFile
                                 A QGIS plugin
 This extract the distribution of one vector layer in each feature of a second vector layer
                             -------------------
        begin                : 2017-03-05
        copyright            : (C) 2017 by Kevin Bourrand
        email                : k.bourrand@hotmail.fr
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load VectorDistributionExtractionPerFile class from file VectorDistributionExtractionPerFile.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .vector_distribution_extraction_per_file import VectorDistributionExtractionPerFile
    return VectorDistributionExtractionPerFile(iface)
