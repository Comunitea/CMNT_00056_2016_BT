import shelve

d = shelve.open("devel_cache_file")
db = shelve.open("devel_cache_file_recover")
for k in d:
    try:
        db[k] = d[k]
    except:
        print "cannot recover the key: ", K
d.close()
db.close()
