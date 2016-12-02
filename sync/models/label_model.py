from sync.database import database_execute


def delete_client_data(label):
    sql = 'delete from sites where site=?'
    database_execute(sql, (label,))
    sql = 'delete from keys where site=?'
    database_execute(sql, (label,))
