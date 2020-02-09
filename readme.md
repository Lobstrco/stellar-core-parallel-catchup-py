1. Make sure stellar core is not running:
```bash
sudo service stellar-core stop
```

2. Tweak default settings of postgresql for high-performance:
```text
sudo nano /etc/postgresql/10/main/postgresql.conf
```

Change:
```text
max_locks_per_transaction 5000
max_pred_locks_per_transaction 5000
max_connections 1500
shared_buffers 10GB # (allocate about 25% of total RAM)
```

3. Grant superuser permissions to the user:
```bash
sudo -i -u postgres
psql -c "alter user <db_user> with superuser;"
```

4. Connect a large disk to the server (in early 2020 about 2TB would be enough for history and databases)
```bash
lsblk
# format & create partition if required

sudo mkdir /mnt/storage
sudo mount /dev/sdb1 /mnt/storage
```

5. Move postgresql database to the temporary disk
```bash
sudo service postgresql stop
sudo mv sudo mv /var/lib/postgresql/10/main /mnt/storage/
sudo ln -s /mnt/storage/main /var/lib/postgresql/10/main
sudo service postgresql start
```

6. Clone repository
```bash
git clone https://github.com/Lobstrco/stellar-core-parallel-catchup-py.git /mnt/storage/core-parallel-catchup
sudo chown stellar /mnt/storage/core-parallel-catchup
```

7. Login as stellar user
```bash
sudo -i -u stellar
cd src
```

8. Generate your secret key
```bash
stellar-core gen-seed
```

9. Initialize folders structure, daemonize workers monitor and merge process. This will take a while:
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

10. Great! You're almost done. Now rename database:
```sql
ALTER DATABASE "catchup-stellar-result" RENAME TO "stellar-core";
```

11. Move folders to their real destinations:
```bash
sudo mv result/data/buckets /var/lib/stellar/
sudo service postgresql stop
sudo rm /var/lib/postgresql/10/main
sudo mv /mnt/storage/main /var/lib/postgresql/10/
sudo service postgresql start
```

12. Publish history to the cloud.
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
