import pymysql

# This line tricks Django into thinking you have mysqlclient 2.2.1 installed
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()