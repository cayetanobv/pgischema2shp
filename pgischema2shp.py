# -*- coding: utf-8 -*-
#
#  Author: Cayetano Benavent, 2015.
#  https://github.com/GeographicaGS/
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

######################################################################
# Before execute this script you need a CONFIGFILE properly          #
# formed (See CONFIGFILE_example) in your current/working directory. #
######################################################################


import os
import shutil
import psycopg2
import getpass
import logging



def getLayerList(my_database, my_password, my_user, my_host, my_port, my_query):
    """
    Get a list of layers to export from PostGIS (You must define a SQL Query)

    """

    logger.info("Getting data from PostGIS...")

    try:
        conn = psycopg2.connect(database=my_database, user=my_user,
        password=my_password, host=my_host, port=my_port)

        cur = conn.cursor()
        cur.execute(my_query)

        res = cur.fetchall()

        cur.close()
        conn.close()

        return res

    except Exception as err:
        logger.error(err)


def exportShp01(tables, folder, my_password, my_database, my_user, my_host, my_port):
    """
    With ogr2ogr

    """

    logger.info("Exporting layers from PostGIS to shp...")

    try:
        fmt = '-f "ESRI Shapefile"'
        connpar = 'PG:"host={0} user={1} dbname={2} password={3} port={4}"'.format(my_host,
                                                my_user, my_database, my_password, my_port)

        for t in tables:
            shpfolder = os.path.join(folder, t[1])
            createFolder(shpfolder)

            shpname = os.path.join(folder, t[1])
            tablename = '{0}.{1}'.format(t[0], t[1])
            cmd = 'ogr2ogr {0} {1} {2} {3}'.format(fmt, shpname, connpar, tablename)
            os.system(cmd)

            zipShp(shpname)
            removeFolder(shpfolder)

    except Exception as err:
        logger.error(err)


def exportShp02(tables, folder, my_password, my_database, my_user, my_host, my_port):
    """
    With pgsql2shp

    """

    logger.info("Exporting layers from PostGIS to shp...")

    try:

        for t in tables:

            shpfolder = os.path.join(folder, t[1])
            createFolder(shpfolder)

            shpname = os.path.join(shpfolder, t[1])
            tablename = '{0}.{1}'.format(t[0], t[1])
            cmd = 'pgsql2shp -f "{0}" -h {1} -u {2} -p {3} -P {4} {5} {6}'.format(shpname,
                        my_host, my_user, my_port, my_password, my_database, tablename)
            os.system(cmd)

            zipShp(shpfolder)
            removeFolder(shpfolder)

    except Exception as err:
        logger.error(err)


def zipShp(folder):
    """
    Zip shapefile folder

    """
    try:
        logger.info("Zipping shp layers: {}.zip".format(folder))
        shutil.make_archive(folder, 'zip', folder)

    except Exception as err:
        logger.error(err)


def createFolder(shpfolder):
    """
    Create a folder to store all files from each shapefile

    """
    if not os.path.exists(shpfolder):
        os.makedirs(shpfolder)


def removeFolder(shpfolder):
    """
    Removing shapefile folders (after zip)

    """
    shutil.rmtree(shpfolder)


def readConfigFile(pathtoconfig):
    """
    Reading config file and storing it in a dictionary
    """
    try:
        with open(pathtoconfig) as f:
            lns = f.read().splitlines()

        confg_lst = [l.strip().split('=') for l in lns if '=' in l]

    except Exception as err:
        logger.error(err)

    return {k: val for (k, val) in confg_lst}


def getQuery(querytype, dbschema):
    qry = """
          SELECT table_schema, table_name
             FROM information_schema.tables
             WHERE table_schema='{}';""".format(dbschema)

    if querytype == "views":
        qry = "{} AND table_type='VIEW';".format(qry[:-1])

    elif querytype == "tables":
        qry = "{} AND table_type='BASE TABLE';".format(qry[:-1])

    return qry


def getPsw(my_user):
    """
    Get password from shell
    """
    msg = "Enter password for user {}: ".format(my_user)
    return getpass.getpass(msg)


def main():

    pathtoconfig = "CONFIGFILE"
    cfg_dict = readConfigFile(os.path.join(os.getcwd(), pathtoconfig))

    my_database = cfg_dict.get("DATABASE")
    my_user = cfg_dict.get("USER")
    my_host = cfg_dict.get("HOST")
    my_port = cfg_dict.get("PORT")
    folder = cfg_dict.get("EXPORTFOLDER")
    dbschema = cfg_dict.get("DBSCHEMA")
    querytype = cfg_dict.get("QUERYTYPE")
    engine = cfg_dict.get("ENGINE")
    my_password = getPsw(my_user)
    my_query = getQuery(querytype, dbschema)

    tb = getLayerList(my_database, my_password, my_user, my_host, my_port, my_query)

    if tb:
        if engine == "ogr2ogr":
            exportShp01(tb, folder, my_password, my_database, my_user, my_host, my_port)

        elif engine == "pgsql2shp":
            exportShp02(tb, folder, my_password, my_database, my_user, my_host, my_port)

        else:
            logger.error("There is no engine to export layers... Define 'pgsql2shp' or 'ogr2ogr'.")

    else:
        logger.error("There are not layers to export. Check DB schema...")


if __name__ == "__main__":

    logfmt = "[%(asctime)s - %(levelname)s] - %(message)s"
    dtfmt = "%Y-%m-%d %I:%M:%S"
    logging.basicConfig(level=logging.INFO, format=logfmt, datefmt=dtfmt)
    logger = logging.getLogger()

    main()
