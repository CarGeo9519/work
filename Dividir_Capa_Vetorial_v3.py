"""
/***************************************************************************
 SplitLayerByField
                                 A QGIS plugin
 Divide una capa vectorial en múltiples capas basadas en valores únicos de un campo
 Versión final corregida para QGIS 3.40.4
 ***************************************************************************/
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterString,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingException,
    QgsVectorFileWriter,
    QgsFeatureRequest,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils
)
from qgis.PyQt.QtCore import QCoreApplication

class SplitLayerByField(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    FIELD = 'FIELD'
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    PREFIX_EXPRESSION = 'PREFIX_EXPRESSION'
    INCLUDE_FIELD_VALUE = 'INCLUDE_FIELD_VALUE'
    OUTPUT_FORMAT = 'OUTPUT_FORMAT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SplitLayerByField()

    def name(self):
        return 'splitlayerbyfield'

    def displayName(self):
        return self.tr('Dividir capa por campo (avanzado)')

    def group(self):
        return self.tr('Herramientas personalizadas')

    def groupId(self):
        return 'customtools'

    def shortHelpString(self):
        return self.tr("""
        Divide una capa vectorial en múltiples capas basadas en valores únicos de un campo seleccionado.

        Características:
        - Permite definir un prefijo usando expresiones
        - Opción para incluir o no el valor del campo en el nombre
        - Exporta a GPKG, SHP, GeoJSON, CSV o KML
        """)

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.INPUT,
            self.tr('Capa de entrada'),
            [QgsProcessing.TypeVectorAnyGeometry]
        ))

        self.addParameter(QgsProcessingParameterField(
            self.FIELD,
            self.tr('Campo para dividir'),
            parentLayerParameterName=self.INPUT
        ))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.OUTPUT_FOLDER,
            self.tr('Carpeta de salida')
        ))

        self.addParameter(QgsProcessingParameterString(
            self.PREFIX_EXPRESSION,
            self.tr('Expresión para prefijo'),
            defaultValue="'TABLA_' || \"Tramo\" || '_'",
            optional=True
        ))

        self.addParameter(QgsProcessingParameterBoolean(
            self.INCLUDE_FIELD_VALUE,
            self.tr('Incluir valor del campo en el nombre'),
            defaultValue=True
        ))

        self.addParameter(QgsProcessingParameterEnum(
            self.OUTPUT_FORMAT,
            self.tr('Formato de salida'),
            options=['ESRI Shapefile', 'GeoPackage', 'GeoJSON', 'CSV', 'KML'],
            defaultValue=1
        ))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        field_name = self.parameterAsString(parameters, self.FIELD, context)
        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        prefix_expression = self.parameterAsString(parameters, self.PREFIX_EXPRESSION, context)
        include_field_value = self.parameterAsBoolean(parameters, self.INCLUDE_FIELD_VALUE, context)
        output_format_index = self.parameterAsInt(parameters, self.OUTPUT_FORMAT, context)

        format_options = {
            0: ('shp', 'ESRI Shapefile'),
            1: ('gpkg', 'GPKG'),
            2: ('geojson', 'GeoJSON'),
            3: ('csv', 'CSV'),
            4: ('kml', 'KML')
        }
        file_extension, driver_name = format_options[output_format_index]

        if layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        field_index = layer.fields().indexFromName(field_name)
        if field_index == -1:
            raise QgsProcessingException(self.tr(f'El campo {field_name} no existe en la capa'))

        expression = None
        context_exp = None
        if prefix_expression.strip():
            expression = QgsExpression(prefix_expression)
            if expression.hasParserError():
                raise QgsProcessingException(self.tr(f'Error en la expresión: {expression.parserErrorString()}'))
            context_exp = QgsExpressionContext()
            context_exp.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))

        unique_values = layer.uniqueValues(field_index)
        total = len(unique_values)
        feedback.pushInfo(self.tr(f'Dividiendo en {total} archivos...'))

        for i, value in enumerate(unique_values):
            if feedback.isCanceled():
                break

            expr_filter = f'"{field_name}" = \'{value}\'' if isinstance(value, str) else f'"{field_name}" = {value}'
            request = QgsFeatureRequest().setFilterExpression(expr_filter)
            filtered_layer = layer.materialize(request)

            safe_value = str(value).replace('/', '_').replace('\\', '_').replace(':', '_')

            prefix = ''
            if expression and context_exp:
                try:
                    feature = next(filtered_layer.getFeatures())
                    context_exp.setFeature(feature)
                    prefix = expression.evaluate(context_exp)
                    if expression.hasEvalError():
                        feedback.pushWarning(self.tr(f'Error evaluando expresión: {expression.evalErrorString()}'))
                        prefix = ''
                except StopIteration:
                    feedback.pushWarning(self.tr(f'Sin datos para el valor {value}'))
                    continue

            if include_field_value:
                file_name = f"{prefix}{safe_value}" if prefix else safe_value
            else:
                file_name = prefix if prefix else 'split_feature'

            file_name = ''.join(c for c in file_name if c.isalnum() or c in ('_', '-')).strip('_')
            output_path = f"{output_folder}/{file_name}.{file_extension}"

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = driver_name
            options.fileEncoding = "UTF-8"
            if driver_name == 'GPKG':
                options.layerName = file_name[:50]

            error_code, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                filtered_layer,
                output_path,
                context.transformContext(),
                options
            )

            if error_code != QgsVectorFileWriter.NoError:
                feedback.pushWarning(self.tr(f'Error exportando {value}: {error_message}'))
            else:
                feedback.pushInfo(self.tr(f'Archivo creado: {output_path}'))

            feedback.setProgress(int((i + 1) / total * 100))

        return {self.OUTPUT_FOLDER: output_folder}
