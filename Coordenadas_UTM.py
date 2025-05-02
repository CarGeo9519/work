#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterCrs,
    QgsProcessingParameterFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsField,
    QgsFields,
    QgsFeatureSink,
    QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant

class Cuadro2x2Poligono(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    FIELD_ID = 'FIELD_ID'
    FIELD_X = 'FIELD_X'
    FIELD_Y = 'FIELD_Y'
    CRS = 'CRS'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Tabla de entrada'))
        self.addParameter(QgsProcessingParameterField(self.FIELD_ID, 'Campo de ID', parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterField(self.FIELD_X, 'Campo X (Este)', parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterField(self.FIELD_Y, 'Campo Y (Norte)', parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterCrs(self.CRS, 'CRS de salida', defaultValue='EPSG:6370'))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Polígonos generados'))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        field_id = self.parameterAsString(parameters, self.FIELD_ID, context)
        field_x = self.parameterAsString(parameters, self.FIELD_X, context)
        field_y = self.parameterAsString(parameters, self.FIELD_Y, context)
        crs = self.parameterAsCrs(parameters, self.CRS, context)

        fields = QgsFields()
        fields.append(QgsField("ID", QVariant.String))
        # Coordenadas de cada vértice
        for punto in ["SW", "SE", "NW", "NE", "Centro"]:
            fields.append(QgsField(f"X_{punto}", QVariant.Double))
            fields.append(QgsField(f"Y_{punto}", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.Polygon, crs)

        for feature in layer.getFeatures():
            try:
                id_val = str(feature[field_id])
                x = float(feature[field_x])
                y = float(feature[field_y])
            except Exception as e:
                feedback.reportError(f"Error en feature ID {feature.id()}: {e}")
                continue

            # Definir las esquinas y centro
            coords = {
                "SW": (x, y),
                "SE": (x + 2, y),
                "NE": (x + 2, y + 2),
                "NW": (x, y + 2),
                "Centro": (x + 1, y + 1)
            }

            # Crear polígono (en orden)
            puntos_poligono = [QgsPointXY(*coords["SW"]),
                               QgsPointXY(*coords["SE"]),
                               QgsPointXY(*coords["NE"]),
                               QgsPointXY(*coords["NW"]),
                               QgsPointXY(*coords["SW"])]  # cerrar el polígono

            f = QgsFeature(fields)
            f.setGeometry(QgsGeometry.fromPolygonXY([puntos_poligono]))
            f.setAttribute("ID", id_val)
            for punto, (px, py) in coords.items():
                f.setAttribute(f"X_{punto}", px)
                f.setAttribute(f"Y_{punto}", py)

            sink.addFeature(f, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def name(self):
        return 'cuadro_2x2_poligono'

    def displayName(self):
        return 'Generar polígono 2x2 m desde esquina suroeste'

    def group(self):
        return 'Herramientas Personalizadas'

    def groupId(self):
        return 'herramientas_personalizadas'

    def createInstance(self):
        return Cuadro2x2Poligono()

