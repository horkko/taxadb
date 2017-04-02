#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
from taxadb.taxadb import TaxaDB
from taxadb.accessionid import AccessionID
from taxadb.taxid import TaxID
from taxadb.schema import Accession, Taxa
from taxadb.util import md5_check, fatal
from nose.plugins.attrib import attr
from testconfig import config


class TestMainFunc(unittest.TestCase):
    """Class to test global methods"""

    @attr('main')
    def test_max_limit_exceeded(self):
        """Check max length of ids raises an exception"""
        ids = [i for i in range(1, 1001)]
        with self.assertRaises(SystemExit):
            TaxaDB.check_list_ids(ids)

    @attr('main')
    def test_max_limit_ok(self):
        ids = [i for i in range(1, 90)]
        self.assertTrue(TaxaDB.check_list_ids(ids))

    @attr('main')
    def test_wrong_dbtype(self):
        """Check wrong dbtype raises an exception"""
        with self.assertRaises(SystemExit):
            TaxaDB(dbtype='fake')


class TestUtils(unittest.TestCase):
    """Class to test taxadb.util"""

    @attr('util')
    @attr('main')
    def test_md5check_success(self):
        """Check md5 is ok"""
        okfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              'good.txt')
        self.assertIsNone(md5_check(okfile))

    @attr('util')
    @attr('main')
    def test_md5check_fails(self):
        """Check md5 fails"""
        badfile = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'wrong.txt')
        with self.assertRaises(AssertionError):
            md5_check(badfile)

    @attr('util')
    @attr('main')
    def test_fatal_throws(self):
        """Check fatal throws SystemExit"""
        with self.assertRaises(SystemExit):
            fatal("failed")


class TestTaxadb(unittest.TestCase):
    """Main class to test AccessionID and TaxID method with sqlite"""

    def setUp(self):
        # Set attributes
        self.dbtype = None
        self.username = None
        self.password = None
        self.hostname = None
        self.port = None
        self.dbname = None
        self.testdir = os.path.dirname(os.path.realpath(__file__))
        self.back_env = None

        # If config does not contains key sql, it means no config file passed
        #  on command line
        # so we default to sqlite test
        if 'sql' not in config:
            config['sql'] = {'dbtype': 'sqlite',
                             'dbname': 'taxadb/test/test_db.sqlite'}

        self.dbtype = config['sql']['dbtype']
        # Defaults to sqlite
        if self.dbtype is None or self.dbtype == '':
            self.dbtype = 'sqlite'
        if self.dbtype not in ['postgres', 'mysql', 'sqlite']:
            self.fail("dbtype option %s not supported" % str(self.dbtype))

        self.dbname = config['sql']['dbname']
        # Defaults to sqlite test database
        if self.dbname is None or self.dbname == '':
            self.dbname = 'taxadb/test/test_db.sqlite'

        if 'username' in config['sql'] \
                and config['sql']['username'] is not None:
            self.username = config['sql']['username']
        if 'password' in config['sql'] \
                and config['sql']['password'] is not None:
            self.password = config['sql']['password']
        if 'hostname' in config['sql'] \
                and config['sql']['hostname'] is not None:
            self.hostname = config['sql']['hostname']
        if 'port' in config['sql'] and config['sql']['port']:
            self.port = int(config['sql']['port'])
        self._unset_user_env()

    def tearDown(self):
        """Remove previously stuff set"""
        self._set_config_back()

    def _buildTaxaDBObject(self, obj):
        sql = obj(dbname=self.dbname, dbtype=self.dbtype,
                  username=self.username, password=self.password,
                  hostname=self.hostname, port=self.port)
        return sql

    def _unset_user_env(self):
        """If user has set TAXADB_CONFIG we remove it for our tests"""
        if os.environ.get('TAXADB_CONFIG') is not None:
            del os.environ['TAXADB_CONFIG']

    def _set_config_from_envvar(self):
        """Set configuration, from config file and set env variable"""
        cfg = os.path.join(self.testdir, 'taxadb.cfg')
        if not os.path.exists(cfg):
            raise Exception("Can't find taxadb.cfg %s" % str(cfg))
        if os.environ.get('TAXADB_CONFIG') is not None:
            self.back_env = os.environ.get('TAXADB_CONFIG')
            del os.environ['TAXADB_CONFIG']
        os.environ['TAXADB_CONFIG'] = cfg

    def _set_config_back(self):
        """Remove env variable"""
        if self.back_env is not None:
            os.environ['TAXADB_CONFIG'] = self.back_env
            self.back_env = None
        return self.back_env

    @attr('main')
    def test_table_exists_ok(self):
        """Check the method return True when checking ofr existsing table"""
        obj = self._buildTaxaDBObject(TaxaDB)
        self.assertTrue(obj.check_table_exists(Accession))
        self.assertTrue(obj.check_table_exists(Taxa))

    @attr('config')
    @attr('main')
    def test_setconfig_from_envvar(self):
        """Check using configuration from environment variable is ok"""
        self._set_config_from_envvar()
        db = AccessionID()
        self.assertEqual(db.get('dbname'), 'taxadb/test/test_db.sqlite')
        self.assertEqual(db.get('dbtype'), 'sqlite')

    @attr('config.1')
    @attr('main')
    def test_setconfig_nodbname_raises(self):
        """Check method raises SystemExit when no dbname set"""
        with self.assertRaises(SystemExit):
            db = AccessionID(dbtype='sqlite')

    @attr('config')
    @attr('main')
    def test_setconfig_from_configfile(self):
        """Check passing a configuration file is ok"""
        db = AccessionID(config=os.path.join(self.testdir, 'taxadb.cfg'))
        self.assertEqual(db.get('dbname'), 'taxadb/test/test_db.sqlite')
        self.assertEqual(db.get('dbtype'), 'sqlite')

    @attr('config')
    @attr('main')
    def test_set_args(self):
        """Check we can set config from dict as args"""
        db = AccessionID(dbtype='sqlite',
                         dbname=os.path.join(self.testdir, 'test_db.sqlite'))
        self.assertEqual(db.get('dbtype'), 'sqlite')
        self.assertEqual(os.path.basename(db.get('dbname')), 'test_db.sqlite')

    @attr('config')
    @attr('main')
    def test_set_config_with_wrong_section(self):
        """Check we catch exception by using config file with wrong section"""
        with self.assertRaises(SystemExit):
            db = AccessionID(config=os.path.join(self.testdir,
                                                 'taxadb-nosection.cfg'))

    @attr('config')
    @attr('main')
    def test_get_config_nooption(self):
        """Check get method returns None when an option is not found in the 
        configurtion file"""
        db = AccessionID(config=os.path.join(self.testdir, 'taxadb.cfg'))
        self.assertIsNone(db.get('unknown'))

    @attr('config')
    @attr('main')
    def test_set_config_option_unset_section(self):
        """Check set throws AttributeError as required section for settings 
        option is not defined yet"""
        db = AccessionID(config=os.path.join(self.testdir, 'taxadb.cfg'))
        with self.assertRaises(AttributeError):
            db.set('newoption', 'newvalue', section="UNSET_SECCTION")

    @attr('getdb')
    @attr('main')
    def test_getdatabase_nouser_or_nopasswd(self):
        """Check get_database throws SystemExit when no user or no password
         is set"""
        with self.assertRaises(SystemExit):
            db = AccessionID(dbname='taxadb', dbtype='mysql')

    @attr('getdb')
    @attr('main')
    def test_getdatabase_mysql_nohostname_noport_setdefault(self):
        """Check get_database set default hostname and port for MySQL"""
        try:
            db = AccessionID(dbname='taxadb', dbtype='mysql',
                             password="123",
                             username="admin")
            self.assertEqual(int(db.get('port')), 3306)
            self.assertEqual(db.get('hostname'), 'localhost')
        except SystemExit as err:
            unittest.skip("Can't test function: %s" % str(err))

    @attr('getdb')
    @attr('main')
    def test_getdatabase_postgres_nohostname_noport_setdefault(self):
        """Check get_database set default hostname and port for MySQL"""
        try:
            db = AccessionID(dbname='taxadb', dbtype='postgres',
                             password="admin",
                             username="admin")
            self.assertEqual(int(db.get('port')), 5432)
            self.assertEqual(db.get('hostname'), 'localhost')
        except SystemExit as err:
            unittest.skip("Can't test function: %s" % str(err))

    @attr('getdb.1')
    @attr('main')
    def test_getdatabase_sqlite_throws(self):
        """Check get_database throws SystemExit when wrong or unaccessible db"""
        with self.assertRaises(SystemExit):
            db = AccessionID(dbname='/unaccessible', dbtype='sqlite')

    @attr('accessionid')
    @attr('main')
    def test_accession_taxid(self):
        """Check the method get the correct taxid for a given accesion id"""
        accession = self._buildTaxaDBObject(AccessionID)
        taxids = accession.taxid(['X17276'])
        for taxon in taxids:
            self.assertEqual(taxon[0], 'X17276')
            self.assertEqual(taxon[1], 9646)

    @attr('accessionid')
    @attr('main')
    def test_accesion_taxid_null(self):
        """Check method generator throws StopIteration, no results found"""
        accession = self._buildTaxaDBObject(AccessionID)
        taxids = accession.taxid(['111111'])
        with self.assertRaises(StopIteration):
            taxids.__next__()

    @attr('accessionid')
    @attr('main')
    def test_accession_sci_name(self):
        accession = self._buildTaxaDBObject(AccessionID)
        sci_name = accession.sci_name(['Z12029'])
        for taxon in sci_name:
            assert taxon[0] == 'Z12029'
            assert taxon[1] == 'Bos indicus'

    @attr('accessionid')
    @attr('main')
    def test_accesion_sci_name_null(self):
        """Check method generator throws StopIteration, no results found"""
        accession = self._buildTaxaDBObject(AccessionID)
        taxids = accession.sci_name(['111111'])
        with self.assertRaises(StopIteration):
            taxids.__next__()

    @attr('accessionid')
    @attr('main')
    def test_accession_lineage_id(self):
        accession = self._buildTaxaDBObject(AccessionID)
        lineage_id = accession.lineage_id(['X52702'])
        for taxon in lineage_id:
            self.assertEqual(taxon[0], 'X52702')
            self.assertListEqual(taxon[1], [
                9771, 9766, 9765, 9761, 9721, 91561, 314145, 1437010, 9347,
                32525,40674, 32524, 32523, 1338369, 8287, 117571, 117570, 7776,
                7742, 89593, 7711, 33511, 33213, 6072, 33208, 33154, 2759,
                131567])

    @attr('accessionid')
    @attr('main')
    def test_accesion_lineage_id_null(self):
        """Check method generator throws StopIteration, no results found"""
        accession = self._buildTaxaDBObject(AccessionID)
        taxids = accession.sci_name(['111111'])
        with self.assertRaises(StopIteration):
            taxids.__next__()

    @attr('accessionid')
    @attr('main')
    def test_accession_lineage_name(self):
        accession = self._buildTaxaDBObject(AccessionID)
        lineage_name = accession.lineage_name(['X60065'])
        for taxon in lineage_name:
            self.assertEqual(taxon[0], 'X60065')
            self.assertListEqual(taxon[1], [
                'Bos taurus', 'Bos', 'Bovinae', 'Bovidae', 'Pecora',
                'Ruminantia', 'Cetartiodactyla', 'Laurasiatheria',
                'Boreoeutheria', 'Eutheria', 'Theria', 'Mammalia', 'Amniota',
                'Tetrapoda', 'Dipnotetrapodomorpha', 'Sarcopterygii',
                'Euteleostomi', 'Teleostomi', 'Gnathostomata', 'Vertebrata',
                'Craniata', 'Chordata', 'Deuterostomia', 'Bilateria',
                'Eumetazoa', 'Metazoa', 'Opisthokonta', 'Eukaryota',
                'cellular organisms'])

    @attr('accessionid')
    @attr('main')
    def test_accesion_lineage_name_null(self):
        """Check method generator throws StopIteration, no results found"""
        accession = self._buildTaxaDBObject(AccessionID)
        taxids = accession.lineage_name(['111111'])
        with self.assertRaises(StopIteration):
            taxids.__next__()

    @attr('taxid')
    @attr('main')
    def test_taxid_sci_name(self):
        taxid = self._buildTaxaDBObject(TaxID)
        name = taxid.sci_name(37572)
        self.assertEqual(name, 'Papilionoidea')

    @attr('taxid')
    @attr('main')
    def test_taxid_sci_name_None(self):
        """Check method returns None, no results found"""
        taxid = self._buildTaxaDBObject(TaxID)
        name = taxid.sci_name(0000)
        self.assertIsNone(name)

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_id(self):
        taxid = self._buildTaxaDBObject(TaxID)
        lineage = taxid.lineage_id(9986)
        self.assertListEqual(lineage, [
            9986, 9984, 9979, 9975, 314147, 314146, 1437010, 9347, 32525,
            40674, 32524, 32523, 1338369, 8287, 117571, 117570, 7776, 7742,
            89593, 7711, 33511, 33213, 6072, 33208, 33154, 2759, 131567])

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_id_reverse(self):
        taxid = self._buildTaxaDBObject(TaxID)
        lineage = taxid.lineage_id(9986, reverse=True)
        self.assertListEqual(lineage, [
            131567, 2759, 33154, 33208, 6072, 33213, 33511, 7711, 89593,
            7742, 7776, 117570, 117571, 8287, 1338369, 32523, 32524, 40674,
            32525, 9347, 1437010, 314146, 314147, 9975, 9979, 9984, 9986])

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_id_None(self):
        """Check method returns None, no results found"""
        taxid = self._buildTaxaDBObject(TaxID)
        name = taxid.lineage_id(0000)
        self.assertIsNone(name)

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_id_revesrse_None(self):
        """Check method returns None, no results found"""
        taxid = self._buildTaxaDBObject(TaxID)
        name = taxid.lineage_id(0000, reverse=True)
        self.assertIsNone(name)

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_name(self):
        taxid = self._buildTaxaDBObject(TaxID)
        lineage = taxid.lineage_name(33208)
        self.assertListEqual(lineage, ['Metazoa', 'Opisthokonta',
                                       'Eukaryota', 'cellular organisms'])

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_name_reverse(self):
        taxid = self._buildTaxaDBObject(TaxID)
        lineage = taxid.lineage_name(33208, reverse=True)
        self.assertListEqual(lineage, ['cellular organisms', 'Eukaryota',
                                       'Opisthokonta', 'Metazoa'])

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_name_None(self):
        """Check method returns None, no results found"""
        taxid = self._buildTaxaDBObject(TaxID)
        name = taxid.lineage_name(0000)
        self.assertIsNone(name)

    @attr('taxid')
    @attr('main')
    def test_taxid_lineage_name_reverse_None(self):
        """Check method returns None, no results found"""
        taxid = self._buildTaxaDBObject(TaxID)
        name = taxid.lineage_name(0000, reverse=True)
        self.assertIsNone(name)

    @attr('taxid')
    @attr('main')
    def test_taxid_unmapped_taxid_throws(self):
        """Check method throws SystemExit on demand"""
        taxid = self._buildTaxaDBObject(TaxID)
        with self.assertRaises(SystemExit):
            taxid._unmapped_taxid(0000, do_exit=True)
        self.assertTrue(taxid._unmapped_taxid(0000))

