from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsWkbTypes,
    QgsFeatureSink,
    QgsProcessingParameterPoint,
    QgsProcessingParameterDefinition,
    QgsCoordinateTransform,
    QgsProject,
    QgsFeature,
    QgsGeometry,
)
from qgis.PyQt.QtCore import QVariant
import random

HelpMessage = (
    'Euclidean Distance: Imagine you are walking in a straight line from one point to another. This is the shortest path, like flying directly from one place to another.\r\n'
    'Manhattan Distance: Imagine you are walking in a city with streets laid out in a grid. You can only walk along the streets, not through buildings. This means you have to take a path that goes around the blocks.\r\n'
    'In summary:\r\n'
    'Euclidean Distance is the straight-line distance.\r\n'
    'Manhattan Distance is the distance you travel along the grid streets. (This plugin follows North-South-East-West orientation.)\r\n'
    'Note: All distance calculations are performed in the CRS (coordinate reference system) of the input polygon layer.r\n'
    '\r\n'
    'ユークリッド距離: 2点間を直線で結んだ最短距離です。まっすぐ歩く、または空を飛ぶイメージです。\r\n'
    'マンハッタン距離: 碁盤目状の街を歩くように、縦横の道だけを使って移動する距離です。建物を突っ切ることはできません。\r\n'
    'まとめ:\r\n'
    'ユークリッド距離は直線距離です。\r\n'
    'マンハッタン距離は縦横の道に沿った距離です（本プラグインでは東西南北方向を想定）。\r\n'
    '注意: 距離計算は入力ポリゴンレイヤの座標参照系(CRS)で行われます。'
)

class YardingDistanceBase:
    """Shared utility methods for yarding distance algorithms."""

    def generate_points(self, geom, spacing, distribution):
        from qgis.core import QgsPointXY, QgsGeometry
        points = []
        if distribution == 0:  # Grid
            bbox = geom.boundingBox()
            xmin, xmax = bbox.xMinimum(), bbox.xMaximum()
            ymin, ymax = bbox.yMinimum(), bbox.yMaximum()
            x = xmin
            while x <= xmax:
                y = ymin
                while y <= ymax:
                    pt = QgsPointXY(x, y)
                    if geom.contains(QgsGeometry.fromPointXY(pt)):
                        points.append(pt)
                    y += spacing
                x += spacing
        else:  # Random
            area = geom.area()
            if area == 0:
                return []
            num_points = int(area / (spacing * spacing))
            num_points = min(num_points, 10000)
            bbox = geom.boundingBox()
            xmin, xmax = bbox.xMinimum(), bbox.xMaximum()
            ymin, ymax = bbox.yMinimum(), bbox.yMaximum()
            attempts = 0
            max_attempts = num_points * 10
            while len(points) < num_points and attempts < max_attempts:
                rx = random.uniform(xmin, xmax)
                ry = random.uniform(ymin, ymax)
                pt = QgsPointXY(rx, ry)
                if geom.contains(QgsGeometry.fromPointXY(pt)):
                    points.append(pt)
                attempts += 1
        return points

    def get_dist_method_str(self, dist_method):
        return 'Euclidean' if dist_method == 0 else 'Manhattan'

    def reproject_geom(self, geom, transform):
        g = QgsGeometry(geom)
        g.transform(transform)
        return g

    def check_projected_crs(self, crs):
        if crs.isGeographic():
            raise Exception(
                "The input polygon layer must use a projected CRS (not a geographic/latitude-longitude CRS). Please reproject the layer and try again. ポリゴンレイヤを投影座標系に再投影してください。\n"
                f"Current CRS: {crs.authid()}"
            )

    def get_transform(self, src_crs, dest_crs):
        if src_crs != dest_crs:
            return QgsCoordinateTransform(src_crs, dest_crs, QgsProject.instance())
        return None

    def log_point_fields(self):
        from qgis.core import QgsFields, QgsField
        fields = QgsFields()
        fields.append(QgsField('polygon_id', QVariant.Int))
        fields.append(QgsField('nearest_yarding_id', QVariant.Int))
        fields.append(QgsField('min_dist', QVariant.Double))
        fields.append(QgsField('dist_method', QVariant.String))
        return fields

    def line_fields(self):
        from qgis.core import QgsFields, QgsField
        fields = QgsFields()
        fields.append(QgsField('log_id', QVariant.Int))
        fields.append(QgsField('yarding_id', QVariant.Int))
        fields.append(QgsField('dist', QVariant.Double))
        fields.append(QgsField('dist_method', QVariant.String))
        return fields

    def polygon_fields(self, polygon_layer):
        from qgis.core import QgsField
        fields = polygon_layer.fields()
        fields.append(QgsField('mean_yarding_dist', QVariant.Double))
        fields.append(QgsField('dist_method', QVariant.String))
        return fields

    def yarding_fields(self, point_layer):
        from qgis.core import QgsField
        fields = point_layer.fields()
        fields.append(QgsField('yarding_id', QVariant.Int))
        fields.append(QgsField('mean_yarding_dist', QVariant.Double))
        fields.append(QgsField('dist_method', QVariant.String))
        return fields

class YardingDistanceAlgorithm(QgsProcessingAlgorithm, YardingDistanceBase):
    INPUT_POLYGON = 'INPUT_POLYGON'
    INPUT_POINTS = 'INPUT_POINTS'
    DIST_METHOD = 'DIST_METHOD'
    GRID_SPACING = 'GRID_SPACING'
    POINT_DISTRIBUTION = 'POINT_DISTRIBUTION'
    OUTPUT_LOG_POINTS = 'OUTPUT_LOG_POINTS'
    OUTPUT_LINES = 'OUTPUT_LINES'
    OUTPUT_POLYGON = 'OUTPUT_POLYGON'
    OUTPUT_YARDING_POINTS = 'OUTPUT_YARDING_POINTS'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_POLYGON, 'Harvest Area Polygon 伐区', [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_POINTS, 'Yarding Point 土場', [QgsProcessing.TypeVectorPoint]))

        # Distance Calculation Method (advanced)
        p = QgsProcessingParameterEnum(
            self.DIST_METHOD, 'Distance Calculation Method 距離計算方法', options=['Euclidean', 'Manhattan'], defaultValue=0)
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(p)

        # Grid Spacing (advanced)
        p = QgsProcessingParameterNumber(
            self.GRID_SPACING, 'Grid Spacing (meters) 点群間隔', type=QgsProcessingParameterNumber.Double,
            defaultValue=25, minValue=0.0001
        )
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(p)

        # Log Point Distribution (advanced)
        p = QgsProcessingParameterEnum(
            self.POINT_DISTRIBUTION, 'Log Point Distribution 点群の配置', options=['Grid', 'Random'], defaultValue=0
        )
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(p)

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_YARDING_POINTS, 'Mean Yarding Distance (Yarding Point)', QgsProcessing.TypeVectorPoint))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_POLYGON, 'Mean Yarding Distance (Harvest Area)', QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_LINES, 'Log-Yarding Line', QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_LOG_POINTS, 'Log Points', QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        polygon_layer = self.parameterAsSource(parameters, self.INPUT_POLYGON, context)
        point_layer = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        polygon_crs = polygon_layer.sourceCrs()
        self.check_projected_crs(polygon_crs)
        dist_method = self.parameterAsEnum(parameters, self.DIST_METHOD, context)
        dist_method_str = self.get_dist_method_str(dist_method)
        spacing = self.parameterAsDouble(parameters, self.GRID_SPACING, context)
        point_distribution = self.parameterAsEnum(parameters, self.POINT_DISTRIBUTION, context)  # 0: Grid, 1: Random

        point_crs = point_layer.sourceCrs()
        transform = self.get_transform(point_crs, polygon_crs)
        need_transform = transform is not None

        log_point_fields = self.log_point_fields()
        line_fields = self.line_fields()
        polygon_fields = self.polygon_fields(polygon_layer)
        yarding_fields = self.yarding_fields(point_layer)
        yarding_stats = {}

        log_point_features = []
        line_features = []
        polygon_features = []

        yarding_feats = list(point_layer.getFeatures())
        for polygon_feat in polygon_layer.getFeatures():
            geom = polygon_feat.geometry()
            polygon_id = polygon_feat.id()
            points = self.generate_points(geom, spacing, point_distribution)

            log_id = 0
            for pt in points:
                min_dist = None
                nearest_yarding_id = None
                nearest_yarding_pt = None
                for yarding_feat in yarding_feats:
                    yarding_pt = yarding_feat.geometry().asPoint()
                    if need_transform:
                        yarding_pt = transform.transform(yarding_pt)
                    if dist_method == 0:
                        dist = ((pt.x() - yarding_pt.x()) ** 2 + (pt.y() - yarding_pt.y()) ** 2) ** 0.5
                    else:
                        dist = abs(pt.x() - yarding_pt.x()) + abs(pt.y() - yarding_pt.y())
                    if min_dist is None or dist < min_dist:
                        min_dist = dist
                        nearest_yarding_id = yarding_feat.id()
                        nearest_yarding_pt = yarding_pt
                log_feat = QgsFeature(log_point_fields)
                log_feat.setGeometry(QgsGeometry.fromPointXY(pt))
                log_feat.setAttributes([polygon_id, nearest_yarding_id, min_dist, dist_method_str])
                log_point_features.append(log_feat)
                line_feat = QgsFeature(line_fields)
                line_feat.setGeometry(QgsGeometry.fromPolylineXY([pt, nearest_yarding_pt]))
                line_feat.setAttributes([log_id, nearest_yarding_id, min_dist, dist_method_str])
                line_features.append(line_feat)
                log_id += 1
                if nearest_yarding_id not in yarding_stats:
                    yarding_stats[nearest_yarding_id] = []
                yarding_stats[nearest_yarding_id].append(min_dist)
            if points:
                mean_dist = sum([f['min_dist'] for f in log_point_features if f['polygon_id'] == polygon_id]) / len(points)
            else:
                mean_dist = None
            poly_feat = QgsFeature(polygon_fields)
            poly_feat.setGeometry(geom)
            attrs = list(polygon_feat.attributes())
            attrs.append(mean_dist)
            attrs.append(dist_method_str)
            poly_feat.setAttributes(attrs)
            polygon_features.append(poly_feat)

        yarding_features = []
        for yarding_feat in yarding_feats:
            mean_dist = None
            if yarding_feat.id() in yarding_stats and yarding_stats[yarding_feat.id()]:
                mean_dist = sum(yarding_stats[yarding_feat.id()]) / len(yarding_stats[yarding_feat.id()])
            y_feat = QgsFeature(yarding_fields)
            geom = yarding_feat.geometry()
            if need_transform:
                geom = self.reproject_geom(geom, transform)
            y_feat.setGeometry(geom)
            attrs = list(yarding_feat.attributes())
            attrs.append(yarding_feat.id())
            attrs.append(mean_dist)
            attrs.append(dist_method_str)
            y_feat.setAttributes(attrs)
            yarding_features.append(y_feat)

        (polygon_sink, polygon_id) = self.parameterAsSink(parameters, self.OUTPUT_POLYGON, context,
                                                          polygon_fields, QgsWkbTypes.Polygon, polygon_layer.sourceCrs())
        for f in polygon_features:
            polygon_sink.addFeature(f, QgsFeatureSink.FastInsert)
        (log_points_sink, log_points_id) = self.parameterAsSink(parameters, self.OUTPUT_LOG_POINTS, context,
                                                                log_point_fields, QgsWkbTypes.Point, polygon_layer.sourceCrs())
        for f in log_point_features:
            log_points_sink.addFeature(f, QgsFeatureSink.FastInsert)
        (lines_sink, lines_id) = self.parameterAsSink(parameters, self.OUTPUT_LINES, context,
                                                      line_fields, QgsWkbTypes.LineString, polygon_layer.sourceCrs())
        for f in line_features:
            lines_sink.addFeature(f, QgsFeatureSink.FastInsert)
        (yarding_sink, yarding_id) = self.parameterAsSink(parameters, self.OUTPUT_YARDING_POINTS, context,
                                                          yarding_fields, QgsWkbTypes.Point, point_layer.sourceCrs())
        for f in yarding_features:
            yarding_sink.addFeature(f, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT_LOG_POINTS: log_points_id,
            self.OUTPUT_YARDING_POINTS: yarding_id,
            self.OUTPUT_LINES: lines_id,
            self.OUTPUT_POLYGON: polygon_id
        }

    def name(self):
        return 'yarding_distance'

    def displayName(self):
        return 'Yarding Distance (point layer)'

    def createInstance(self):
        return YardingDistanceAlgorithm()
    
    def shortHelpString(self):
        return HelpMessage

class YardingDistanceSinglePointAlgorithm(QgsProcessingAlgorithm, YardingDistanceBase):
    INPUT_POLYGON = 'INPUT_POLYGON'
    INPUT_POINT = 'INPUT_POINT'
    DIST_METHOD = 'DIST_METHOD'
    GRID_SPACING = 'GRID_SPACING'
    POINT_DISTRIBUTION = 'POINT_DISTRIBUTION'
    OUTPUT_LOG_POINTS = 'OUTPUT_LOG_POINTS'
    OUTPUT_LINES = 'OUTPUT_LINES'
    OUTPUT_POLYGON = 'OUTPUT_POLYGON'
    OUTPUT_YARDING_POINTS = 'OUTPUT_YARDING_POINTS'
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT_POLYGON, 'Harvest Area Polygon 伐区', [QgsProcessing.TypeVectorPolygon]))

        self.addParameter(QgsProcessingParameterPoint(
            self.INPUT_POINT, 'Yarding Point (Click on Map) 土場をクリック', defaultValue=None))

        # Distance Calculation Method (advanced)
        p = QgsProcessingParameterEnum(
            self.DIST_METHOD, 'Distance Calculation Method 距離計算方法', options=['Euclidean', 'Manhattan'], defaultValue=0)
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(p)

        # Grid Spacing (advanced)
        p = QgsProcessingParameterNumber(
            self.GRID_SPACING, 'Grid Spacing (meters) 点群間隔', type=QgsProcessingParameterNumber.Double,
            defaultValue=25, minValue=0.0001
        )
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(p)

        # Log Point Distribution (advanced)
        p = QgsProcessingParameterEnum(
            self.POINT_DISTRIBUTION, 'Log Point Distribution 点群の配置', options=['Grid', 'Random'], defaultValue=0
        )
        p.setFlags(p.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(p)

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_YARDING_POINTS, 'Mean Yarding Distance (Yarding Point)', QgsProcessing.TypeVectorPoint))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_POLYGON, 'Mean Yarding Distance (Harvest Area)', QgsProcessing.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_LINES, 'Log-Yarding Line', QgsProcessing.TypeVectorLine))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_LOG_POINTS, 'Log Points', QgsProcessing.TypeVectorPoint))

    def processAlgorithm(self, parameters, context, feedback):
        from qgis.core import QgsFields, QgsField, QgsFeature, QgsGeometry
        polygon_layer = self.parameterAsSource(parameters, self.INPUT_POLYGON, context)
        polygon_crs = polygon_layer.sourceCrs()
        self.check_projected_crs(polygon_crs)
        yarding_point = self.parameterAsPoint(parameters, self.INPUT_POINT, context)
        dist_method = self.parameterAsEnum(parameters, self.DIST_METHOD, context)
        dist_method_str = self.get_dist_method_str(dist_method)
        spacing = self.parameterAsDouble(parameters, self.GRID_SPACING, context)
        point_distribution = self.parameterAsEnum(parameters, self.POINT_DISTRIBUTION, context)

        input_point_crs = None
        if hasattr(context, 'project') and context.project():
            input_point_crs = context.project().crs()
        if input_point_crs is None:
            input_point_crs = QgsProject.instance().crs()
        transform = self.get_transform(input_point_crs, polygon_crs)
        need_transform = transform is not None
        if need_transform:
            yarding_point = transform.transform(yarding_point)

        log_point_fields = QgsFields()
        log_point_fields.append(QgsField('polygon_id', QVariant.Int))
        log_point_fields.append(QgsField('min_dist', QVariant.Double))
        log_point_fields.append(QgsField('dist_method', QVariant.String))

        line_fields = QgsFields()
        line_fields.append(QgsField('log_id', QVariant.Int))
        line_fields.append(QgsField('dist', QVariant.Double))
        line_fields.append(QgsField('dist_method', QVariant.String))

        polygon_fields = self.polygon_fields(polygon_layer)
        yarding_fields = QgsFields()
        yarding_fields.append(QgsField('yarding_id', QVariant.Int))
        yarding_fields.append(QgsField('mean_yarding_dist', QVariant.Double))
        yarding_fields.append(QgsField('dist_method', QVariant.String))

        log_point_features = []
        line_features = []
        polygon_features = []
        yarding_features = []
        all_dists = []

        for polygon_feat in polygon_layer.getFeatures():
            geom = polygon_feat.geometry()
            polygon_id = polygon_feat.id()
            points = self.generate_points(geom, spacing, point_distribution)

            log_id = 0
            dists = []
            for pt in points:
                if dist_method == 0:
                    dist = ((pt.x() - yarding_point.x()) ** 2 + (pt.y() - yarding_point.y()) ** 2) ** 0.5
                else:
                    dist = abs(pt.x() - yarding_point.x()) + abs(pt.y() - yarding_point.y())
                dists.append(dist)
                all_dists.append(dist)
                log_feat = QgsFeature(log_point_fields)
                log_feat.setGeometry(QgsGeometry.fromPointXY(pt))
                log_feat.setAttributes([polygon_id, dist, dist_method_str])
                log_point_features.append(log_feat)
                line_feat = QgsFeature(line_fields)
                line_feat.setGeometry(QgsGeometry.fromPolylineXY([pt, yarding_point]))
                line_feat.setAttributes([log_id, dist, dist_method_str])
                line_features.append(line_feat)
                log_id += 1
            if dists:
                mean_dist = sum(dists) / len(dists)
            else:
                mean_dist = None
            poly_feat = QgsFeature(polygon_fields)
            poly_feat.setGeometry(geom)
            attrs = list(polygon_feat.attributes())
            attrs.append(mean_dist)
            attrs.append(dist_method_str)
            poly_feat.setAttributes(attrs)
            polygon_features.append(poly_feat)

        mean_yarding_dist = sum(all_dists) / len(all_dists) if all_dists else None
        yarding_feat = QgsFeature(yarding_fields)
        yarding_feat.setGeometry(QgsGeometry.fromPointXY(yarding_point))
        yarding_feat.setAttributes([0, mean_yarding_dist, dist_method_str])
        yarding_features.append(yarding_feat)

        (polygon_sink, polygon_id) = self.parameterAsSink(parameters, self.OUTPUT_POLYGON, context,
                                                          polygon_fields, QgsWkbTypes.Polygon, polygon_layer.sourceCrs())
        for f in polygon_features:
            polygon_sink.addFeature(f, QgsFeatureSink.FastInsert)
        (log_points_sink, log_points_id) = self.parameterAsSink(parameters, self.OUTPUT_LOG_POINTS, context,
                                                                log_point_fields, QgsWkbTypes.Point, polygon_layer.sourceCrs())
        for f in log_point_features:
            log_points_sink.addFeature(f, QgsFeatureSink.FastInsert)
        (lines_sink, lines_id) = self.parameterAsSink(parameters, self.OUTPUT_LINES, context,
                                                      line_fields, QgsWkbTypes.LineString, polygon_layer.sourceCrs())
        for f in line_features:
            lines_sink.addFeature(f, QgsFeatureSink.FastInsert)
        (yarding_sink, yarding_id) = self.parameterAsSink(parameters, self.OUTPUT_YARDING_POINTS, context,
                                                          yarding_fields, QgsWkbTypes.Point, polygon_layer.sourceCrs())
        for f in yarding_features:
            yarding_sink.addFeature(f, QgsFeatureSink.FastInsert)

        return {
            self.OUTPUT_LOG_POINTS: log_points_id,
            self.OUTPUT_YARDING_POINTS: yarding_id,
            self.OUTPUT_LINES: lines_id,
            self.OUTPUT_POLYGON: polygon_id
        }

    def name(self):
        return 'yarding_distance_single_point'

    def displayName(self):
        return 'Yarding Distance (click on map)'

    def createInstance(self):
        return YardingDistanceSinglePointAlgorithm()
    
    def shortHelpString(self):
        return HelpMessage

def create_algorithms():
    return [YardingDistanceAlgorithm(), YardingDistanceSinglePointAlgorithm()]