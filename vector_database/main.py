from vector_database import Database

abteilungs_name = "Einkaufsabteilung"

path_to_db = "/home/jakobschiller/devour/data_extraction/vector-database/database"

einkaufs_db = Database(path_to_db, abteilungs_name)

einkaufs_db.database.delete_collection(abteilungs_name)

einkaufs_db = Database(path_to_db, abteilungs_name)

einkaufs_db.vectorise("/home/jakobschiller/devour/data_extraction/vector-database/purchasing_departement", 5)

print(einkaufs_db.employee_info, einkaufs_db.collection.count())

