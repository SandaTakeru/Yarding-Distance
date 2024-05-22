"""
Model exported as python.
Name : Yarding Distance
Group : Yarding Distance
With QGIS : 32804
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterPoint
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterDefinition
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsExpression
import processing


class YardingDistanceAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource('logging_area', 'Logging Area', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        param = QgsProcessingParameterNumber('dots_spacing_m', 'Dots spacing (m)', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=25)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        """ param = QgsProcessingParameterEnum('dots_pattern', 'Dots Pattern', options=['Aligned','Randomized'], allowMultiple=False, usesStaticStrings=False, defaultValue=[0])
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param) """
        self.addParameter(QgsProcessingParameterPoint('yarding_point', 'Yarding Point', defaultValue='0.000000,0.000000'))
        self.addParameter(QgsProcessingParameterFeatureSink('YardingPoint', 'Yarding Point', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue='TEMPORARY_OUTPUT'))
        self.addParameter(QgsProcessingParameterFeatureSink('DotsInLoggingArea', 'Dots in Logging Area', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterFeatureSink('TransportGraph', 'Transport Graph', type=QgsProcessing.TypeVectorLine, createByDefault=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterFeatureSink('YardingDistanceLabel', 'Yarding Distance Label', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(15, model_feedback)
        results = {}
        outputs = {}

        # A1_Reproject a layer
        alg_params = {
            'INPUT': parameters['logging_area'],
            'OPERATION': '',
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['A1_reprojectALayer'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # A2_Geometry repair
        alg_params = {
            'INPUT': outputs['A1_reprojectALayer']['OUTPUT'],
            'METHOD': 1,  # Structure
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['A2_geometryRepair'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # A3_Create a spatial index
        alg_params = {
            'INPUT': outputs['A2_geometryRepair']['OUTPUT']
        }
        outputs['A3_createASpatialIndex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # B1_Create a layer from point
        alg_params = {
            'INPUT': parameters['yarding_point'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['B1_createALayerFromPoint'] = processing.run('native:pointtolayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # B2_Add XY field
        alg_params = {
            'CRS': 'ProjectCrs',
            'INPUT': outputs['B1_createALayerFromPoint']['OUTPUT'],
            'PREFIX': 'point_',
            'OUTPUT': parameters['YardingPoint']
        }
        outputs['B2_addXyField'] = processing.run('native:addxyfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['YardingPoint'] = outputs['B2_addXyField']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}
    
        # C1_Aligned dots
        alg_params = {
            'CRS': 'ProjectCrs',
            'EXTENT': outputs['A3_createASpatialIndex']['OUTPUT'],
            'INSET': 0,
            'IS_SPACING': True,
            'RANDOMIZE': False,
            'SPACING': parameters['dots_spacing_m'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['C1_Aligned_dots'] = processing.run('qgis:regularpoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}
        
        """ # C1_Random points in polygons
        alg_params = {
            'INCLUDE_POLYGON_ATTRIBUTES': True,
            'INPUT': outputs['A3_createASpatialIndex']['OUTPUT'],
            'MAX_TRIES_PER_POINT': 10,
            'MIN_DISTANCE': 0,
            'MIN_DISTANCE_GLOBAL': 0,
            'POINTS_NUMBER': QgsExpression('area($geometry)/(25*25)').evaluate(),
            'SEED': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['C1_Random_points_in_polygons'] = processing.run('native:randompointsinpolygons', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {} """

        # C2_Create a spatial index
        """ if parameters['dots_pattern'] == 'Aligned':
            alg_params = {
                'INPUT': outputs['C1_Aligned_dots']['OUTPUT']
            }
        #elif parameters['dots_pattern'] == 'Randomized':
        alg_params = {
            'INPUT': outputs['C1_Random_points_in_polygons']['OUTPUT']
        }
        #else:
            #print('error2') """
        
        alg_params = {
            'INPUT': outputs['C1_Aligned_dots']['OUTPUT']
        }

        outputs['C2_createASpatialIndex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # C3_Extraction by location
        alg_params = {
            'INPUT': outputs['C2_createASpatialIndex']['OUTPUT'],
            'INTERSECT': outputs['A3_createASpatialIndex']['OUTPUT'],
            'PREDICATE': [0],  # intersect
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['C3_extractionByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # C4_Create a spatial index
        alg_params = {
            'INPUT': outputs['C3_extractionByLocation']['OUTPUT']
        }
        outputs['C4_createASpatialIndex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # C5_Add XY field
        alg_params = {
            'CRS': 'ProjectCrs',
            'INPUT': outputs['C4_createASpatialIndex']['OUTPUT'],
            'PREFIX': 'area_',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['C5_addXyField'] = processing.run('native:addxyfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # D1_Nearest Neighbor Join of Attributes
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELDS_TO_COPY': [''],
            'INPUT': outputs['C5_addXyField']['OUTPUT'],
            'INPUT_2': outputs['B2_addXyField']['OUTPUT'],
            'MAX_DISTANCE': None,
            'NEIGHBORS': 1,
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['D1_nearestNeighborJoinOfAttributes'] = processing.run('native:joinbynearest', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # D2_Attribute refactoring
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"id"','length': 10,'name': 'id','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'expression': '"area_x"','length': 20,'name': 'area_x','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"area_y"','length': 20,'name': 'area_y','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"point_x"','length': 20,'name': 'point_x','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"point_y"','length': 20,'name': 'point_y','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': '"distance"','length': 20,'name': 'EuclideanDistance','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'abs("area_x" - "point_x") +\nabs("area_y" - "point_y")','length': 20,'name': 'ManhattanDistance','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'abs("area_x" - "point_x")','length': 20,'name': 'Distance_xAxis','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'abs("area_y" - "point_y")','length': 20,'name': 'Distance_yAxis','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['D1_nearestNeighborJoinOfAttributes']['OUTPUT'],
            'OUTPUT': parameters['DotsInLoggingArea']
        }
        outputs['D2_attributeRefactoring'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['DotsInLoggingArea'] = outputs['D2_attributeRefactoring']['OUTPUT']

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # D3_Create a spatial index
        alg_params = {
            'INPUT': outputs['D2_attributeRefactoring']['OUTPUT']
        }
        outputs['D3_createASpatialIndex'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # D4_Distance of the nearest hub (line to the hub)
        alg_params = {
            'FIELD': 'id',
            'HUBS': outputs['B2_addXyField']['OUTPUT'],
            'INPUT': outputs['C5_addXyField']['OUTPUT'],
            'UNIT': 0,  # Meters
            'OUTPUT': parameters['TransportGraph']
        }
        outputs['D4_distanceOfTheNearestHubLineToTheHub'] = processing.run('qgis:distancetonearesthublinetohub', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['TransportGraph'] = outputs['D4_distanceOfTheNearestHubLineToTheHub']['OUTPUT']

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # E1_Join attributes by location (summary)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['A3_createASpatialIndex']['OUTPUT'],
            'JOIN': outputs['D3_createASpatialIndex']['OUTPUT'],
            'JOIN_FIELDS': QgsExpression("'EuclideanDistance;ManhattanDistance'").evaluate(),
            'PREDICATE': [0],  # intersect
            'SUMMARIES': [6],  # mean
            'OUTPUT': parameters['YardingDistanceLabel']
        }
        outputs['E1_joinAttributesByLocationSummary'] = processing.run('qgis:joinbylocationsummary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['YardingDistanceLabel'] = outputs['E1_joinAttributesByLocationSummary']['OUTPUT']
        return results

    def name(self):
        return 'Yarding Distance'

    def displayName(self):
        return 'Polygon to Coordinate'

    def group(self):
        return 'calculate the Average Yarding Distance'

    def groupId(self):
        return 'Yarding Distance'

    def shortHelpString(self):
        return ''

    def createInstance(self):
        return YardingDistanceAlgorithm()
