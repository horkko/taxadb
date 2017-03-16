from taxadb.schema import db, DatabaseFactory
from taxadb.util import fatal
import sys
import os


class TaxaDB(object):
    """Main TaxaDB package class

    Parent class of the Taxadb application. Use this class to create inheriting
    classes.

    Args:
        dbname (:obj:`str`): Database name to connect to, default to
        TAXADB_DBNAME
        dbtype (:obj:`str`): Database type to connect to (`sqlite`, `postgre`,
            `mysql`). Default TAXADB_DBTYPE then to `sqlite`
        **kwargs: Arbitrary arguments. Supported (username, password, port,
            hostname)

    Raises:
        AttributeError: If dbtype not supported
        AttributeError: If dbname is None
        AttributeError: If cannot instantiate `taxadb.schema.DatabaseFactory`.
    Attributes:
        MAX_LIST (:obj:`int`): Maximum number of bind variables to pass to
            request methods. Due to SQLite limit of passed arguments to a
            statement, we limit number of accession and taxid to
            request to 999 (https://www.sqlite.org/c3ref/bind_blob.html)
    """

    MAX_LIST = 999

    def __init__(self, dbname=None, dbtype=None, **kwargs):
        self.db = None
        self.dbname = None
        self.dbtype = None
        taxadbtype = dbtype
        if taxadbtype is None:
            if 'TAXADB_DBTYPE' in os.environ:
                taxadbtype = os.environ.get('TAXADB_DBTYPE')
            else:
                taxadbtype = 'sqlite'
        if taxadbtype not in DatabaseFactory.SUPPORTED_DBS:
            raise AttributeError(
                "Database type '%s' not supported %s"
                % (str(taxadbtype), str(DatabaseFactory.SUPPORTED_DBS)))
        taxadbname = dbname
        if 'TAXADB_DBNAME' in os.environ and taxadbname is None:
            taxadbname = os.environ.get('TAXADB_DBNAME')
        if taxadbname is None:
            raise AttributeError("A database name is required")

        self.dbname = taxadbname
        self.dbtype = taxadbtype
        try:
            self.database = DatabaseFactory(
                dbname=self.dbname,
                dbtype=self.dbtype,
                **kwargs).get_database()
        except AttributeError as err:
            fatal("Can't create database object: %s" % str(err))
        self.db = db
        self.db.initialize(self.database)
        self.db.connect()

    def __del__(self):
        """Ensure database connection is closed"""
        if self.db is not None and not self.db.is_closed():
            self.db.close()

    @classmethod
    def check_table_exists(cls, table):
        """Check a table exists in the database

        Args:
            table (:obj:`str`): Database `table` name to check.

        Returns:
            True

        Raises:
             SystemExit: if `table` does not exist
        """
        if not table.table_exists():
            fatal("Table %s does not exist" % (str(table._meta.db_table)))
        return True

    @staticmethod
    def check_list_ids(ids):
        """Check the list of ids is not longer that MAX_LIST

        Args:
            ids (:obj:`list`): List of bind values

        Returns:
            True

        Raises:
            SystemExit: If `len` of the list of greater than `MAX_LIST`.
        """
        if len(ids) > TaxaDB.MAX_LIST:
            fatal("Too many accession entries to request (%d), max %d" % (
                        len(ids), TaxaDB.MAX_LIST))
        return True

    def get_database(self):
        """Returns `peewee.database` object"""
        return self.database

    def get_dbname(self):
        """Returns database name we are connected to"""
        return self.dbname

    def get_dbtype(self):
        """Returns the database type we are working with"""
        return self.dbtype

    def _unmapped_taxid(self, acc, do_exit=False):
        """Prints an error message on stderr an accession number is not mapped
            with a taxid

        Source ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/README
        >> If for some reason the source organism cannot be mapped to the
        taxonomy database, the column will contain 0.<<

        Args:
            acc (:obj:`str`): Accession number not mapped with taxid
            do_exit (:obj:`bool`): Exit with code 1. Default False
        """
        print("No taxid mapped for accession %s" % str(acc), file=sys.stderr)
        if do_exit:
            sys.exit(1)
        return True
