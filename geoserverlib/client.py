import os
import json
import logging
import urllib
import urlparse

import requests


logger = logging.getLogger('geoserverlib.client')


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

    def create_feature_type(self, workspace, datastore, view, sql_query):
        """
        Mimicks XML cUrl command, for example:

        curl -u admin:geoserver -XPOST -T xml/featuretype.xml -H 'Content-type: text/xml' http://localhost:${GEOSERVER_PORT}/geoserver/rest/workspaces/deltaportaal/datastores/deltaportaal/featuretypes

        """
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores', datastore,
                                          'featuretypes'])
        headers = {'content-type': 'application/json'}
        payload = {
            'featureType': {
                'name': view,
                'nativeName': view,
                'namespace': {
                    'name': workspace,
                    'href': url(self.base_url, ['/geoserver/rest/namespaces',
                                                '%s.json' % workspace])
                },
                'title': view,
                'keywords': {
                    'string': [view, 'features']
                },
                'nativeCRS': ('GEOGCS["WGS 84", DATUM["World Geodetic System '
                              '1984", SPHEROID["WGS 84", 6378137.0, '
                              '298.257223563, AUTHORITY["EPSG","7030"]], '
                              'AUTHORITY["EPSG","6326"]], PRIMEM["Greenwich", '
                              '0.0, AUTHORITY["EPSG","8901"]], '
                              'UNIT["degree", 0.017453292519943295], '
                              'AXIS["Geodetic longitude", EAST], '
                              'AXIS["Geodetic latitude", NORTH], '
                              'AUTHORITY["EPSG","4326"]]'),
                'srs': 'EPSG:28992',
                'nativeBoundingBox': {
                    'crs': 'EPSG:4326',
                    'maxx': 211954.375,
                    'maxy': 510710.812500007,
                    'minx': 63947.1821375899,
                    'miny': 358627.978623543
                },
                'latLonBoundingBox': {
                    'crs': ('GEOGCS["WGS84(DD)", DATUM["WGS84", '
                            'SPHEROID["WGS84", 6378137.0, 298.257223563]], '
                            'PRIMEM["Greenwich", 0.0], UNIT["degree", '
                            '0.017453292519943295], '
                            'AXIS["Geodetic longitude", EAST], '
                            'AXIS["Geodetic latitude", NORTH]]'),
                    'maxx': 211954.375,
                    'maxy': 510710.812500007,
                    'minx': 63947.1821375899,
                    'miny': 358627.978623543
                },
                'projectionPolicy': 'FORCE_DECLARED',
                'enabled': True,
                'advertised': True,
                'metadata': {
                    'entry': {
                        '@key': 'JDBC_VIRTUAL_TABLE',
                        'virtualTable': {
                            ## THESE LINES SHOULD BE COMMENTED, DOES NOT
                            ## WORK WITH IT. THROWS ILLEGAL JSON EXCEPTION.
                            ## AS XML IT DOES NOT THROW AN EXCEPTION.
                            # 'geometry': {
                            #     'name': 'the_geom',
                            #     'srid': -1,
                            #     'type': 'Geometry'
                            # },
                            'name': view,
                            'sql': sql_query
                        }
                    }
                },
                'store': {
                    '@class': 'dataStore',
                    'href': url(self.base_url, ['/geoserver/rest/workspaces',
                                                workspace, 'datastores',
                                                '%s.json' % datastore]),
                    'name': workspace
                },
                'maxFeatures': 0,
                'numDecimals': 0,
                'attributes': {
                    'attribute': [{
                        'binding': 'java.lang.Double',
                        'maxOccurs': 1,
                        'minOccurs': 0,
                        'name': 'waterstand_actueel',
                        'nillable': True
                    }, {
                        'binding': ('com.vividsolutions.jts.geom.'
                                    'MultiLineString'),
                        'maxOccurs': 1,
                        'minOccurs': 0,
                        'name': 'the_geom',
                        'nillable': True
                    }, {
                        'binding': 'java.lang.Short',
                        'maxOccurs': 1,
                        'minOccurs': 0,
                        'name': 'kilometer',
                        'nillable': True
                    }]
                }
            }
        }
        response = requests.post(request_url, data=json.dumps(payload),
                                 headers=headers, auth=self.auth)
        success_msg = "view '%s' created successfully" % view
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

    def create_style(self, style_name, style_filename):
        """

        cURL examples:
        curl -u admin:geoserver -XPOST -H 'Content-type: text/xml' -d '<style><name>deltaportaal</name><filename>deltaportaal.sld</filename></style>' http://localhost:${GEOSERVER_PORT}/geoserver/rest/styles
        curl -u admin:geoserver -XPUT -H 'Content-type: application/vnd.ogc.sld+xml' -d @xml/deltaportaal.sld http://localhost:${GEOSERVER_PORT}/geoserver/rest/styles/deltaportaal

        """
        request_url = url(self.base_url, ['/geoserver/rest/styles'])
        headers = {'content-type': 'application/json'}
        payload = {
            'style': {
                'name': style_name,
                'filename': os.path.split(style_filename)[1]
            }
        }
        response = requests.post(request_url, data=json.dumps(payload),
                                 headers=headers, auth=self.auth)
        if response.ok:
            request_url = url(self.base_url, ['/geoserver/rest/styles',
                                              style_name])
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
