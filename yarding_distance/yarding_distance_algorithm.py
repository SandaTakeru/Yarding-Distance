"""
Model exported as python.
Name : Yarding Distance
Group : Yarding Distance
With QGIS : 32804
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterPoint,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsExpression
)
import processing

class YardingDistanceAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource('logging_area', 'Logging Area 伐区', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        param = QgsProcessingParameterNumber('dots_spacing_m', 'Dots spacing 点群間隔 (m)', type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=25)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterEnum('dots_pattern', 'Dots Pattern 点群配置', options=['Aligned 等間隔','Randomized ランダム'], allowMultiple=False, usesStaticStrings=False, defaultValue='Aligned 等間隔')
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterPoint('yarding_point', 'Yarding Point 集材点', defaultValue='0.000000,0.000000'))
        
        # Define parameters
        parameters = [
            ('YardingPoint', 'Yarding Point 集材点', QgsProcessing.TypeVectorAnyGeometry, None),
            ('DotsInLoggingArea', 'Dots in Logging Area 伐区内点群', QgsProcessing.TypeVectorAnyGeometry, None),
            ('YardingGraph', 'Yarding Graph 集材グラフ', QgsProcessing.TypeVectorLine, None),
            ('YardingDistanceLabel', 'Yarding Distance Label 平均集材距離ラベル', QgsProcessing.TypeVectorAnyGeometry, None)
        ]

        # Add parameters
        for param in parameters:
            self.addParameter(QgsProcessingParameterFeatureSink(*param, createByDefault=True, supportsAppend=True))
        
    def processAlgorithm(self, parameters, context, model_feedback):

        # Define a function to run the algorithm and update the feedback
        def run_algorithm(algorithm, parameters, outputs, context, feedback):
            output = processing.run(algorithm, parameters, context=context, feedback=feedback, is_child_algorithm=True)
            if feedback.isCanceled():
                return {}
            return output

        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the overall progress through the model
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
        outputs['A1_reprojectALayer'] = run_algorithm('native:reprojectlayer', alg_params, outputs, context, feedback)

        # A2_Geometry repair
        alg_params = {
            'INPUT': outputs['A1_reprojectALayer']['OUTPUT'],
            'METHOD': 1,  # Structure
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['A2_geometryRepair'] = run_algorithm('native:fixgeometries', alg_params, outputs, context, feedback)

        # A3_Create a spatial index
        alg_params = {
            'INPUT': outputs['A2_geometryRepair']['OUTPUT']
        }
        outputs['A3_createASpatialIndex'] = run_algorithm('native:createspatialindex', alg_params, outputs, context, feedback)


        # B1_Create a layer from point
        alg_params = {
            'INPUT': parameters['yarding_point'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['B1_createALayerFromPoint'] = run_algorithm('native:pointtolayer', alg_params, outputs, context, feedback)

        # B2_Add XY field
        alg_params = {
            'CRS': 'ProjectCrs',
            'INPUT': outputs['B1_createALayerFromPoint']['OUTPUT'],
            'PREFIX': 'point_',
            'OUTPUT': parameters['YardingPoint']
        }
        outputs['B2_addXyField'] = run_algorithm('native:addxyfields', alg_params, outputs, context, feedback)
        results['YardingPoint'] = outputs['B2_addXyField']['OUTPUT']

        # C1_Aligned dots
        if parameters['dots_pattern'] == 0: #Aligned
            alg_params = {
                'CRS': 'ProjectCrs',
                'EXTENT': outputs['A3_createASpatialIndex']['OUTPUT'],
                'INSET': 0,
                'IS_SPACING': True,
                'RANDOMIZE': False,
                'SPACING': parameters['dots_spacing_m'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['C1_Aligned_dots'] = run_algorithm('qgis:regularpoints', alg_params, outputs, context, feedback)
            C2_input = outputs['C1_Aligned_dots']['OUTPUT']

        # C1_Random points inside polygons
        elif parameters['dots_pattern'] == 1: #Randomized
            alg_params = {
                'INPUT': outputs['A3_createASpatialIndex']['OUTPUT'],
                'MIN_DISTANCE': parameters['dots_spacing_m']/(2**0.5),
                'STRATEGY': 1,  # Points density
                'VALUE': (parameters['dots_spacing_m'])**-2,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['C1_Random_points_inside_polygons'] = run_algorithm('qgis:randompointsinsidepolygons', alg_params, outputs, context, feedback)
            C2_input = outputs['C1_Random_points_inside_polygons']['OUTPUT']

        else:
            print('error C1 ; Process did not create dots pattern.')

        # C2_Create a spatial index
        alg_params = {'INPUT': C2_input}
        outputs['C2_createASpatialIndex'] = run_algorithm('native:createspatialindex', alg_params, outputs, context, feedback)

        # C3_Extraction by location
        alg_params = {
            'INPUT': outputs['C2_createASpatialIndex']['OUTPUT'],
            'INTERSECT': outputs['A3_createASpatialIndex']['OUTPUT'],
            'PREDICATE': [0],  # intersect
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['C3_extractionByLocation'] = run_algorithm('native:extractbylocation', alg_params, outputs, context, feedback)

        # C4_Create a spatial index
        alg_params = {
            'INPUT': outputs['C3_extractionByLocation']['OUTPUT']
        }
        outputs['C4_createASpatialIndex'] = run_algorithm('native:createspatialindex', alg_params, outputs, context, feedback)

        # C5_Add XY field
        alg_params = {
            'CRS': 'ProjectCrs',
            'INPUT': outputs['C4_createASpatialIndex']['OUTPUT'],
            'PREFIX': 'area_',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['C5_addXyField'] = run_algorithm('native:addxyfields', alg_params, outputs, context, feedback)

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
        outputs['D1_nearestNeighborJoinOfAttributes'] = run_algorithm('native:joinbynearest', alg_params, outputs, context, feedback)

        # D2_Attribute refactoring
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"id"','length': 10,'name': 'id','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},
                               {'expression': '"area_x"','length': 20,'name': 'area_x','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                               {'expression': '"area_y"','length': 20,'name': 'area_y','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                               {'expression': '"point_x"','length': 20,'name': 'point_x','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                               {'expression': '"point_y"','length': 20,'name': 'point_y','precision': 10,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                               {'expression': '"distance"','length': 20,'name': 'EuclideanDistance','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                               {'expression': 'abs("area_x" - "point_x") + abs("area_y" - "point_y")','length': 20,'name': 'ManhattanDistance','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                               {'expression': 'abs("area_x" - "point_x")','length': 20,'name': 'Distance_xAxis','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                               {'expression': 'abs("area_y" - "point_y")','length': 20,'name': 'Distance_yAxis','precision': 12,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
            'INPUT': outputs['D1_nearestNeighborJoinOfAttributes']['OUTPUT'],
            'OUTPUT': parameters['DotsInLoggingArea']
        }
        outputs['D2_attributeRefactoring'] = run_algorithm('native:refactorfields', alg_params, outputs, context, feedback)
        results['DotsInLoggingArea'] = outputs['D2_attributeRefactoring']['OUTPUT']

        # D3_Create a spatial index
        alg_params = {
            'INPUT': outputs['D2_attributeRefactoring']['OUTPUT']
        }
        outputs['D3_createASpatialIndex'] = run_algorithm('native:createspatialindex', alg_params, outputs, context, feedback)

        # D4_Distance of the nearest hub (line to the hub)
        alg_params = {
            'FIELD': 'id',
            'HUBS': outputs['B2_addXyField']['OUTPUT'],
            'INPUT': outputs['C5_addXyField']['OUTPUT'],
            'UNIT': 0,  # Meters
            'OUTPUT': parameters['YardingGraph']
        }
        outputs['D4_distanceOfTheNearestHubLineToTheHub'] = run_algorithm('qgis:distancetonearesthublinetohub', alg_params, outputs, context, feedback)
        results['YardingGraph'] = outputs['D4_distanceOfTheNearestHubLineToTheHub']['OUTPUT']

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
        outputs['E1_joinAttributesByLocationSummary'] = run_algorithm('qgis:joinbylocationsummary', alg_params, outputs, context, feedback)
        results['YardingDistanceLabel'] = outputs['E1_joinAttributesByLocationSummary']['OUTPUT']

        print(outputs)
        print(results)

        feedback.pushInfo("Ending Algorithm")

        return results

    def name(self):
        return 'Yarding Distance 集材距離'

    def displayName(self):
        return 'calculate the Average Yarding Distance 平均集材距離'

    def group(self):
        return None

    def groupId(self):
        return None

    def shortHelpString(self):
        return ''

    def createInstance(self):
        return YardingDistanceAlgorithm()
