import os
import json
import logging
import urllib
import urlparse

import requests


logger = logging.getLogger('geoserverlib.server')


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
        r = requests.get(request_url, headers=headers, auth=self.auth)
        if r.ok:
            return True
        elif r.status_code == 404:
            # workspace does not exist
            return False
        else:
            print "unexpected status code: %s" % r.status_code
            print r.text


    def create_workspace(self, workspace):
        """

        Mimicks XML cUrl command, for example:
        curl -u admin:geoserver -XPOST -H 'Content-type: text/xml' -d '<workspace><name>deltaportaal</name></workspace>' http://localhost:8123/geoserver/rest/workspaces

        """
        if self.workspace_exists(workspace):
            print "workspace '%s' already exists" % workspace
            return False
        request_url = url(self.base_url, ['/geoserver/rest/workspaces'])
        logger.info("request url: %s" % request_url)
        headers = {'content-type': 'application/json'}
        payload = {'workspace': {'name': workspace}}
        r = requests.post(request_url, data=json.dumps(payload),
                          headers=headers, auth=self.auth)
        if r.ok:
            print "workspace '%s' created successfully" % workspace
        else:
            print "NOT OK"
            print r.text
        return r


    def datastore_exists(self, workspace, datastore):
        request_url = url(self.base_url, ['/geoserver/rest/workspaces',
                                          workspace, 'datastores', datastore])
        logger.debug("request url: %s" % request_url)
        headers = {'content-type': 'application/json'}
        r = requests.get(request_url, headers=headers, auth=self.auth)
        if r.ok:
            return True
        elif r.status_code == 404:
            # workspace does not exist
            return False
        else:
            print "unexpected status code: %s" % r.status_code
            print r.text


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
            print "datastore '%s' already exists" % datastore
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
        r = requests.post(request_url, data=json.dumps(payload),
                          headers=headers, auth=self.auth)
        if r.ok:
            print "datastore '%s' created successfully" % datastore
        else:
            print "NOT OK"
            print r.text
        return r


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
        r = requests.post(request_url, data=json.dumps(payload),
                          headers=headers, auth=self.auth)
        if r.ok:
            print "view '%s' created successfully" % view
        else:
            print "NOT OK"
            print r.text
        return r


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
        r = requests.post(request_url, data=json.dumps(payload),
                          headers=headers, auth=self.auth)
        if r.ok:
            request_url = url(self.base_url, ['/geoserver/rest/styles',
                                              style_name])
            xml = open(style_filename, 'r').read()
            headers = {'content-type': 'application/vnd.ogc.sld+xml'}
            r = requests.put(request_url, data=xml, headers=headers,
                             auth=self.auth)
            if r.ok:
                print "style '%s' created successfully" % style_name
            else:
                print "NOT OK"
                print r.text
        else:
            print "NOT OK"
            print r.text
        return r


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
        r = requests.put(request_url, data=json.dumps(payload),
                          headers=headers, auth=self.auth)
        if r.ok:
            print "made '%s' the default style" % style_name
        else:
            print "NOT OK"
            print r.text
        return r


    def show_feature_type(self, workspace, datastore, view, output='xml'):
        """
        Example URL:
        http://localhost:8123/geoserver/rest/workspaces/deltaportaal/\
        datastores/deltaportaal/featuretypes/deltaportaalview.json

        """
        segments = ['/geoserver/rest/workspaces/%s/datastores/%s/featuretypes'
                    % (workspace, datastore), '%s.%s' % (view, output)]
        request_url = url(self.base_url, segments)
        r = requests.get(request_url, auth=self.auth)
        print r.text
