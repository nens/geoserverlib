import os
import json
import logging
import urllib
import urlparse

import requests


logger = logging.getLogger('geoserverlib.client')


class GeoserverClientException(BaseException):
    pass


def url(base, seg, query=None):
    """
    Create a URL from a list of path segments and an optional dict of query
    parameters.

    """
    seg = (urllib.quote(s.strip('/')) for s in seg)
    if query is None or len(query) == 0:
        query_string = ''
    else:
        query_string = "?" + urllib.urlencode(query)
    path = '/'.join(seg) + query_string
    adjusted_base = base.rstrip('/') + '/'
    return urlparse.urljoin(adjusted_base, path)


def process_response(response, success_msg):
    if response.ok:
        logger.info(success_msg)
    else:
        logger.error(response.text)


class GeoserverClient(object):
    """Geoserver client class for storing connection details."""
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = 'http://%s:%s' % (self.host, self.port)
        self.auth = (self.username, self.password)

    def workspace_exists(self, workspace):
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace])
        logger.debug("request url: %s" % request_url)
        headers = {'content-type': 'application/json'}
        response = requests.get(request_url, headers=headers, auth=self.auth)
        if response.ok:
            return True
        elif response.status_code == 404:
            # workspace does not exist
            return False
        else:
            logger.error("unexpected status code: %s (%s)" % (
                response.status_code, response.text))

    def create_workspace(self, workspace):
        """

        Mimicks XML cUrl command, for example:
        curl -u admin:geoserver -XPOST -H 'Content-type: text/xml' -d '<workspace><name>deltaportaal</name></workspace>' http://localhost:8123/geoserver/rest/workspaces

        """
        if self.workspace_exists(workspace):
            print "workspace '%s' already exists" % workspace
            return False
        request_url = url(self.base_url, ['/geoserver/rest/workspaces'])
        logger.debug("request url: %s" % request_url)
        headers = {'content-type': 'application/json'}
        payload = {'workspace': {'name': workspace}}
        response = requests.post(request_url, data=json.dumps(payload),
                                 headers=headers, auth=self.auth)
        success_msg = "workspace '%s' created successfully" % workspace
        process_response(response, success_msg)
        return response

    def delete_workspace(self, workspace):
        """
        cURL example:
        curl -u admin:geoserver -XDELETE -H 'Content-type: text/xml' http://localhost:${GEOSERVER_PORT}/geoserver/rest/workspaces/deltaportaal

        """
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace])
        response = requests.delete(request_url, auth=self.auth)
        success_msg = "deleted workspace '%s'" % workspace
        process_response(response, success_msg)
        return response

    def datastore_exists(self, workspace, datastore):
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores', datastore])
        logger.debug("request url: %s" % request_url)
        headers = {'content-type': 'application/json'}
        response = requests.get(request_url, headers=headers, auth=self.auth)
        if response.ok:
            return True
        elif response.status_code == 404:
            # workspace does not exist
            return False
        else:
            logger.warning("unexpected status code: %s (%s)" % (
                response.status_code, response.text))

    def create_datastore(self, workspace, datastore, connection_parameters):
        """
        Mimicks XML cUrl command, for example:

        curl -u admin:geoserver -XPOST -T xml/datastore.xml -H 'Content-type: text/xml' http://localhost:8123/geoserver/rest/workspaces/deltaportaal/datastores

        Params:
        - connection_parameters, dictionary with database connection info,
        for example:

            connection_parameters = {
                'host': 'localhost',
                'port': '5432',
                'database': 'georest',
                'user': '<username>',
                'passwd': '<password>',
                'dbtype': 'postgis'
            }

        """
        # if datastore exists, return
        if self.datastore_exists(workspace, datastore):
            logger.error("datastore '%s' already exists" % datastore)
            return False
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores'])
        headers = {'content-type': 'application/json'}
        # TODO: make datastore connection parameters configurable
        payload = {
            'dataStore': {
                'name': datastore,
                'connectionParameters': connection_parameters
            }
        }
        response = requests.post(request_url, data=json.dumps(payload),
                                 headers=headers, auth=self.auth)
        success_msg = "datastore '%s' created successfully" % datastore
        process_response(response, success_msg)
        return response

    def delete_datastore(self, workspace, datastore):
        """
        cURL example:
        curl -u admin:geoserver -XDELETE -H 'Content-type: text/xml' http://localhost:${GEOSERVER_PORT}/geoserver/rest/workspaces/deltaportaal/datastores/deltaportaal

        """
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores', datastore])
        response = requests.delete(request_url, auth=self.auth)
        success_msg = "deleted datastore '%s'" % datastore
        process_response(response, success_msg)
        return response

    def create_feature_type(self, workspace, datastore, view, sql_query,
                            srs='EPSG:28992', srid=28992):
        """
        Mimicks XML cUrl command, for example:

        curl -u admin:geoserver -XPOST -T xml/featuretype.xml -H 'Content-type: text/xml' http://localhost:${GEOSERVER_PORT}/geoserver/rest/workspaces/deltaportaal/datastores/deltaportaal/featuretypes

        WARNING: this method is done in XML because of a bug in the GeoServer
        parsing of the VirtualTable in JSON format. In JSON it is not possible
        to add a geometry without getting an IllegalArgumentException. The
        cause is an order problem, since JSON dicts are unordered and XML is
        ordered (see http://jira.codehaus.org/browse/GEOS-4986).

        """
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores', datastore,
                                          'featuretypes'])
        headers = {'content-type': 'text/xml'}
        payload = """
        <featureType>
            <name>%(view)s</name>
            <nativeCRS class="projected">PROJCS["Amersfoort / RD New", GEOGCS["Amersfoort", DATUM["Amersfoort", SPHEROID["Bessel 1841", 6377397.155, 299.1528128, AUTHORITY["EPSG","7004"]], TOWGS84[565.2369, 50.0087, 465.658, -0.40685733032239757, -0.3507326765425626, 1.8703473836067959, 4.0812], AUTHORITY["EPSG","6289"]], PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]], UNIT["degree", 0.017453292519943295], AXIS["Geodetic longitude", EAST], AXIS["Geodetic latitude", NORTH], AUTHORITY["EPSG","4289"]], PROJECTION["Oblique_Stereographic", AUTHORITY["EPSG","9809"]], PARAMETER["central_meridian", 5.387638888888891], PARAMETER["latitude_of_origin", 52.15616055555556], PARAMETER["scale_factor", 0.9999079], PARAMETER["false_easting", 155000.0], PARAMETER["false_northing", 463000.0], UNIT["m", 1.0], AXIS["Easting", EAST], AXIS["Northing", NORTH], AUTHORITY["EPSG","%(srid)s"]]</nativeCRS>
            <srs>%(srs)s</srs>
            <metadata>
                <entry key="cachingEnabled">false</entry>
                <entry key="JDBC_VIRTUAL_TABLE">
                <virtualTable>
                    <name>%(view)s</name>
                    <sql>%(sql_query)s</sql>
                    <geometry>
                        <name>geom</name>
                        <type>Geometry</type>
                        <srid>%(srid)s</srid>
                    </geometry>
                </virtualTable>
                </entry>
            </metadata>
        </featureType>""" % {
            'view': view,
            'sql_query': sql_query,
            'srs': srs,
            'srid': srid
        }
        response = requests.post(request_url, data=payload, headers=headers,
                                 auth=self.auth)
        success_msg = "view '%s' created successfully" % view
        process_response(response, success_msg)
        return response

    def recalculate_bounding_boxes(self, workspace, datastore, view):
        """
        Request for recalculating native and lat/lon bounding boxes.

        """
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores', datastore,
                                          'featuretypes', view])
        headers = {'content-type': 'text/xml'}
        # Need payload, took name resetting, but also requires
        # <enabled>true</enabled> (reported by us through the mailing list).
        xml = '<featureType><name>%s</name><enabled>true</enabled></featureType>' % view
        # WARNING: GeoServer recalculate bug - delimiter is ' in 2.2 rc1, not ,
        request_url = request_url + '?recalculate=nativebbox,latlonbbox'
        response = requests.put(request_url, data=xml,
                                headers=headers, auth=self.auth)
        success_msg = "recalculated bounding boxes for '%s' layer" % view
        process_response(response, success_msg)
        return response

    def delete_layer(self, layer):
        """
        cURL example:
        curl -u admin:geoserver -XDELETE -H 'Content-type: text/xml' http://localhost:${GEOSERVER_PORT}/geoserver/rest/layers/deltaportaalview

        """
        request_url = url(self.base_url, ['/geoserver/rest/layers', layer])
        response = requests.delete(request_url, auth=self.auth)
        success_msg = "deleted '%s' layer" % layer
        process_response(response, success_msg)
        return response

    def delete_feature_type(self, workspace, datastore, layer):
        """
        cURL example:
        curl -u admin:geoserver -XDELETE -H 'Content-type: text/xml' http://localhost:${GEOSERVER_PORT}/geoserver/rest/workspaces/deltaportaal/datastores/deltaportaal/featuretypes/deltaportaalview

        """
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores', datastore,
                                          'featuretypes', layer])
        response = requests.delete(request_url, auth=self.auth)
        success_msg = "deleted '%s' feature type" % layer
        process_response(response, success_msg)
        return response

    def create_style(self, style_name, style_filename=None, style_data=None):
        """

        cURL examples:
        curl -u admin:geoserver -XPOST -H 'Content-type: text/xml' -d '<style><name>deltaportaal</name><filename>deltaportaal.sld</filename></style>' http://localhost:${GEOSERVER_PORT}/geoserver/rest/styles
        curl -u admin:geoserver -XPUT -H 'Content-type: application/vnd.ogc.sld+xml' -d @xml/deltaportaal.sld http://localhost:${GEOSERVER_PORT}/geoserver/rest/styles/deltaportaal

        """
        request_url = url(self.base_url, ['/geoserver/rest/styles'])
        headers = {'content-type': 'application/json'}
        if style_filename:
            filename = os.path.split(style_filename)[1]
        else:
            filename = '%s.sld' % style_name
        payload = {
            'style': {
                'name': style_name,
                'filename': filename
            }
        }
        response = requests.post(request_url, data=json.dumps(payload),
                                 headers=headers, auth=self.auth)
        if response.ok:
            request_url = url(self.base_url, ['/geoserver/rest/styles',
                                              style_name])
            if style_data:
                xml = style_data
            else:
                xml = open(style_filename, 'r').read()
            headers = {'content-type': 'application/vnd.ogc.sld+xml'}
            response = requests.put(request_url, data=xml, headers=headers,
                                    auth=self.auth)
            success_msg = "style '%s' created successfully" % style_name
            process_response(response, success_msg)
        else:
            logger.error(response.text)
        return response

    def delete_style(self, style_name):
        """
        cURL example:
        curl -u admin:geoserver -XDELETE -H 'Content-type: text/xml' http://localhost:${GEOSERVER_PORT}/geoserver/rest/styles/deltaportaal

        """
        request_url = url(self.base_url, ['/geoserver/rest/styles',
                                          style_name])
        response = requests.delete(request_url, auth=self.auth)
        success_msg = "deleted style '%s'" % style_name
        process_response(response, success_msg)
        return response

    def set_default_style(self, workspace, datastore, view, style_name):
        """
        cURL examples:
        curl -u admin:geoserver -XPUT -H 'Content-type: text/xml' -d '<layer><enabled>true</enabled><defaultStyle><name>deltaportaal</name></defaultStyle></layer>' http://localhost:${GEOSERVER_PORT}/geoserver/rest/layers/deltaportaal:deltaportaalview

        """
        request_url = url(self.base_url, ['/geoserver/rest/layers',
                                          '%s:%s' % (workspace, view)])
        headers = {'content-type': 'application/json'}
        payload = {
            'layer': {
                'enabled': True,
                'defaultStyle': {
                    'name': style_name
                }
            }
        }
        response = requests.put(request_url, data=json.dumps(payload),
                                headers=headers, auth=self.auth)
        success_msg = "made '%s' the default style" % style_name
        process_response(response, success_msg)
        return response

    def show_feature_type(self, workspace, datastore, view, output='xml'):
        """
        Example URL:
        http://localhost:8123/geoserver/rest/workspaces/deltaportaal/\
        datastores/deltaportaal/featuretypes/deltaportaalview.json

        """
        segments = ['/geoserver/rest/workspaces/%s/datastores/%s/featuretypes'
                    % (workspace, datastore), '%s.%s' % (view, output)]
        request_url = url(self.base_url, segments)
        response = requests.get(request_url, auth=self.auth)
        print response.text
