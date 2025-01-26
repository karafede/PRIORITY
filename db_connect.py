

import psycopg2


import urllib
pwd = urllib.parse.quote_plus('yourpassword')

def connect_federio_DB_linux():
    # Connect to an existing database
    conn = psycopg2.connect(user="federico", password=pwd, host="192.168.132.222",
                            port="5432", database="rds_22-24", sslmode="disable", gssencmode="disable")
    return (conn)

