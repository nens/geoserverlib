Geoserverlib
============

Introduction
------------

Geoserverlib is a `GeoServer`_ Python client for creating, updating, and deleting workspaces, data stores, feature types, layers and styles on geoservers.

Usage
-----

* instantiate a client::

   from geoserverlib.client import GeoserverClient

   # host, port, username, password for the GeoServer you want to connect to
   client = GeoserverClient(host, port, username, password)

* workspace methods::

   workspace = 'my_workspace'

   client.create_workspace(workspace)
   client.workspace_exists(workspace)  # returns True or False
   client.delete_workspace(workspace)

* datastore methods::

   datastore = 'my_datastore'

   # example connection parameters for postgis datastore
   connection_parameters = {
   	   'host': 'localhost',
	   'port': '5432',
	   'database': '<db_name>',
	   'user': '<db_user>',
	   'password': '<db_password>',
	   'dbtype': 'postgis'
   }
   client.create_datastore(workspace, datastore, connection_parameters)
   client.datastore_exists(workspace, datastore)  # returns True or False
   client.delete_datastore(workspace, datastore)

* feature type and layer methods::

   layer = 'my_layer'

   sql_query = 'SELECT * FROM "<db_table>"'  # layer specific SQL query
   client.create_feature_type(workspace, datastore, layer, sql_query)
   client.delete_layer(layer)
   client.delete_feature_type(workspace, datastore, layer)

* style methods::

   style = 'my_style'

   # create style from file
   style_filename = 'path/to/my_style.sld'
   client.create_style(style, style_filename=style_filename)

   # create style from xml
   style_data = '<xml>style_data</xml>'  # use actual style data here
   client.create_style(style, style_data=style_data)

   # set default style for layer
   client.set_default_style(workspace, datastore, layer, style)

   # delete style
   client.delete_style(style)

* other methods::

   # show the feature type in xml or json
   client.show_feature_type(workspace, datastore, layer, output='xml')

   # recalculate bounding boxes
   client.recalculate_bounding_boxes(workspace, datastore, layer)

.. _GeoServer: http://geoserver.org/display/GEOS/Welcome
