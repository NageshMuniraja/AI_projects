# Database Support Guide

DataInsights AI supports **13 different databases** across traditional RDBMS, cloud data warehouses, and NoSQL systems.

## 📊 Supported Databases

### Traditional RDBMS

#### ✅ PostgreSQL
- **Status**: Production Ready
- **Driver**: `psycopg2-binary`
- **Connection**: Standard host:port with username/password
- **Features**: Full SQL support, JSON queries, advanced analytics

#### ✅ MySQL / MariaDB
- **Status**: Production Ready
- **Driver**: `pymysql`
- **Connection**: Standard host:port with username/password
- **Features**: Full SQL support, compatible with MariaDB

#### ✅ Microsoft SQL Server
- **Status**: Production Ready
- **Driver**: `pymssql`
- **Connection**: Standard host:port with username/password
- **Features**: Full T-SQL support, TOP/OFFSET-FETCH pagination

#### ✅ SQLite
- **Status**: Production Ready
- **Driver**: Built-in Python
- **Connection**: File path only
- **Features**: Embedded database, perfect for demos

#### ⚠️ Oracle Database
- **Status**: Requires Installation
- **Driver**: `oracledb` or `cx-Oracle`
- **Connection**: Host:port with service_name
- **Installation**: `pip install oracledb`
- **Additional**: May require Oracle Instant Client

#### ⚠️ IBM DB2
- **Status**: Requires Installation
- **Driver**: `ibm-db` and `ibm-db-sa`
- **Connection**: Standard host:port with username/password
- **Installation**: `pip install ibm-db ibm-db-sa`
- **Additional**: May require DB2 client libraries

### Cloud Data Warehouses

#### ⚠️ Snowflake
- **Status**: Requires Installation
- **Driver**: `snowflake-connector-python` and `snowflake-sqlalchemy`
- **Connection**: Account URL, warehouse, database, schema
- **Installation**: `pip install snowflake-connector-python snowflake-sqlalchemy`
- **Connection Format**:
  ```python
  {
    "account": "your_account.region",
    "user": "username",
    "password": "password",
    "warehouse": "COMPUTE_WH",
    "database": "DATABASE_NAME",
    "schema": "PUBLIC"
  }
  ```

#### ⚠️ Amazon Redshift
- **Status**: Requires Installation
- **Driver**: `redshift-connector`
- **Connection**: Cluster endpoint with database credentials
- **Installation**: `pip install redshift-connector`
- **Connection Format**:
  ```python
  {
    "host": "cluster-name.region.redshift.amazonaws.com",
    "port": 5439,
    "user": "username",
    "password": "password",
    "database": "dev"
  }
  ```

#### ⚠️ Google BigQuery
- **Status**: Requires Installation
- **Driver**: `google-cloud-bigquery`
- **Connection**: Project ID with service account credentials
- **Installation**: `pip install google-cloud-bigquery google-cloud-bigquery-storage`
- **Connection Format**:
  ```python
  {
    "project_id": "your-gcp-project",
    "dataset": "your_dataset",
    "credentials_json": "{...service account JSON...}"
  }
  ```

### NoSQL Databases

#### ✅ MongoDB
- **Status**: Production Ready
- **Driver**: `pymongo`
- **Connection**: MongoDB URI or host:port
- **Features**: Aggregation pipelines, document queries

#### ⚠️ Apache Cassandra
- **Status**: Requires Installation
- **Driver**: `cassandra-driver`
- **Connection**: Contact points (hosts) and keyspace
- **Installation**: `pip install cassandra-driver`
- **Connection Format**:
  ```python
  {
    "contact_points": ["host1", "host2"],
    "port": 9042,
    "keyspace": "your_keyspace",
    "user": "username",  # optional
    "password": "password"  # optional
  }
  ```

#### ⚠️ Amazon DynamoDB
- **Status**: Requires Installation
- **Driver**: `boto3`
- **Connection**: AWS credentials and region
- **Installation**: `pip install boto3 aioboto3`
- **Connection Format**:
  ```python
  {
    "region": "us-east-1",
    "aws_access_key_id": "YOUR_KEY",
    "aws_secret_access_key": "YOUR_SECRET"
  }
  ```

## 🚀 Quick Installation

### Install All Database Drivers

```bash
cd backend
pip install -r requirements.txt
```

### Install Specific Database Drivers

#### Cloud Data Warehouses
```bash
# Snowflake
pip install snowflake-connector-python==3.6.0 snowflake-sqlalchemy==1.5.1

# Redshift
pip install redshift-connector==2.0.918

# BigQuery
pip install google-cloud-bigquery==3.14.1 google-cloud-bigquery-storage==2.24.0
```

#### Enterprise Databases
```bash
# Oracle
pip install oracledb==2.0.1

# IBM DB2
pip install ibm-db==3.2.3 ibm-db-sa==0.4.0
```

#### NoSQL Databases
```bash
# Cassandra
pip install cassandra-driver==3.28.0

# DynamoDB
pip install boto3==1.34.20 aioboto3==12.3.0
```

## 📝 Connection Examples

### PostgreSQL
```json
{
  "host": "localhost",
  "port": 5432,
  "user": "postgres",
  "password": "password",
  "database": "mydb"
}
```

### Snowflake
```json
{
  "account": "xy12345.us-east-1",
  "user": "username",
  "password": "password",
  "warehouse": "COMPUTE_WH",
  "database": "SALES_DB",
  "schema": "PUBLIC"
}
```

### BigQuery
```json
{
  "project_id": "my-gcp-project",
  "dataset": "analytics",
  "credentials_json": "{...}"
}
```

### MongoDB
```json
{
  "uri": "mongodb://localhost:27017/",
  "database": "mydb"
}
```

### Cassandra
```json
{
  "contact_points": ["localhost"],
  "port": 9042,
  "keyspace": "mykeyspace",
  "user": "cassandra",
  "password": "cassandra"
}
```

## 🔧 Troubleshooting

### Oracle Installation Issues
If you encounter issues with Oracle:
1. Install Oracle Instant Client: https://www.oracle.com/database/technologies/instant-client.html
2. Set environment variables:
   ```bash
   export LD_LIBRARY_PATH=/path/to/instantclient:$LD_LIBRARY_PATH
   ```

### DB2 Installation Issues
If you encounter issues with DB2:
1. Install IBM Data Server Driver
2. May require Visual C++ redistributables on Windows

### Snowflake Connection Issues
- Ensure your account identifier includes region (e.g., `xy12345.us-east-1`)
- Check warehouse is running
- Verify network access (firewall rules)

### BigQuery Authentication
- Download service account JSON key from GCP Console
- Grant BigQuery Data Viewer and Job User roles
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable (optional)

### DynamoDB Permissions
Ensure IAM user/role has:
- `dynamodb:DescribeTable`
- `dynamodb:Query`
- `dynamodb:Scan`
- `dynamodb:GetItem`

## 🎯 Query Syntax Notes

### SQL Databases
All SQL databases support standard SQL with minor dialect differences:
- **Pagination**: PostgreSQL/MySQL use `LIMIT`, SQL Server uses `TOP` or `OFFSET-FETCH`
- **String Concat**: PostgreSQL uses `||`, SQL Server uses `+`

### Snowflake
- Supports advanced analytics (QUALIFY, window functions)
- Use `LIMIT` for pagination
- Zero-copy cloning with `CLONE`

### BigQuery
- Standard SQL syntax
- Partitioned tables with `_PARTITIONTIME`
- Nested and repeated fields

### MongoDB
Queries are JSON aggregation pipelines:
```json
[
  {"collection": "users"},
  {"$match": {"age": {"$gt": 25}}},
  {"$group": {"_id": "$city", "count": {"$sum": 1}}}
]
```

### Cassandra
Uses CQL (Cassandra Query Language):
- Similar to SQL but with restrictions
- Requires PRIMARY KEY in WHERE clause
- Use `ALLOW FILTERING` sparingly

### DynamoDB
Queries are JSON format:
```json
{
  "TableName": "Users",
  "Operation": "query",
  "KeyConditionExpression": "userId = :uid",
  "ExpressionAttributeValues": {":uid": {"S": "123"}}
}
```

## 🔐 Security Best Practices

1. **Never commit credentials** - Use environment variables
2. **Use read-only users** for analytics queries
3. **Enable SSL/TLS** for cloud connections
4. **Rotate credentials** regularly
5. **Use IAM roles** for AWS services (Redshift, DynamoDB)
6. **Use service accounts** for GCP (BigQuery)
7. **Implement network security** (VPC, security groups, firewall rules)

## 📊 Performance Tips

### Snowflake
- Start with smaller warehouses and scale up as needed
- Use clustering keys for large tables
- Enable result caching

### BigQuery
- Use partitioned tables for large datasets
- Avoid `SELECT *` - specify columns
- Use streaming inserts for real-time data

### Redshift
- Use sort keys and distribution keys
- Vacuum and analyze tables regularly
- Use late binding views

### Cassandra
- Design schema for query patterns
- Use appropriate partition keys
- Avoid ALLOW FILTERING in production

## 🆘 Getting Help

- **PostgreSQL/MySQL**: Standard SQL documentation
- **Snowflake**: https://docs.snowflake.com/
- **BigQuery**: https://cloud.google.com/bigquery/docs
- **Redshift**: https://docs.aws.amazon.com/redshift/
- **MongoDB**: https://docs.mongodb.com/
- **Cassandra**: https://cassandra.apache.org/doc/
- **DynamoDB**: https://docs.aws.amazon.com/dynamodb/

## 🎉 Ready to Use

Once installed, all databases will appear in the connection modal with their respective icons and connection forms. The AI agent will automatically generate appropriate queries for each database type!
