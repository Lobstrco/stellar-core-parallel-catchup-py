0. Make sure, stellar core is not running
```bash
sudo service stellar-core stop
```

1. Setup postgresql to allow high load, change values in /etc/postgresql/10/main/postgresql.conf
```text
sudo nano /etc/postgresql/10/main/postgresql.conf

change:
max_locks_per_transaction 5000 (just because)
max_pred_locks_per_transaction 5000
max_connections 1500, minimum: cores_number * (cores_number + 1)
shared_buffers 10GB (up to 25% RAM)
```

2. grant superuser permissions to the user
```bash
sudo -i -u postgres
psql -c "alter user <db_user> with superuser;"
```

3. connect big disk to the server
```bash
lsblk
# format & create partition if required

sudo mkdir /mnt/storage
sudo mount /dev/sdb1 /mnt/storage
```

4. move postgresql database to big disk (about 2TB would be ok for history + databases)
```bash
sudo service postgresql stop
sudo mv sudo mv /var/lib/postgresql/10/main /mnt/storage/
sudo ln -s /mnt/storage/main /var/lib/postgresql/10/main
sudo service postgresql start
```

5. clone repository
```bash
git clone https://github.com/Lobstrco/stellar-core-parallel-catchup-py.git /mnt/storage/core-parallel-catchup
sudo chown stellar /mnt/storage/core-parallel-catchup
```

6. login as stellar user
```bash
sudo -i -u stellar
cd src
```

7. generate your secret key
```bash
stellar-core gen-seed
```

6. initialize folders structure & daemonize workers monitor + merge process
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=<db_user>
export DB_PASSWORD=<db_password>
export NODE_SECRET_KEY=<secret_key> 
python cli.py initialize
nohup python cli.py monitor > monitor.log &
nohup python cli.py merge > merge.log &
```

7. rename database
```sql
ALTER DATABASE "catchup-stellar-result" RENAME TO "stellar-core";
```

8. move folders to their real destinations
```bash
sudo mv result/data/buckets /var/lib/stellar/
sudo service postgresql stop
sudo rm /var/lib/postgresql/10/main
sudo mv /mnt/storage/main /var/lib/postgresql/10/
sudo service postgresql start
```

9. publish history to the cloud.
```text
sudo apt-get install stellar-archivist
sudo service stellar-core stop

sudo -i -u stellar
/bin/bash
export $(cat /etc/stellar/stellar-core | xargs) && stellar-core new-hist s3 --conf /etc/stellar/stellar-core.cfg
exit

sudo service stellar-core start

sudo -i -u stellar
/bin/bash
export $(cat /etc/stellar/stellar-core | xargs) && nohup stellar-archivist repair file:///mnt/storage/parallel-catchup/result/vs/ s3://stellar-archive-<s3_bucket_index>-lobstr --s3region=$AWS_DEFAULT_REGION > archivist-repair.out &
exit
```
