<p align="center">
  <img src="https://raw.githubusercontent.com/dbt-labs/dbt/ec7dee39f793aa4f7dd3dae37282cc87664813e4/etc/dbt-logo-full.svg" alt="dbt logo" width="500"/>
</p>
<p align="center">
  <a href="https://github.com/dbt-labs/dbt-spark/actions/workflows/main.yml">
    <img src="https://github.com/dbt-labs/dbt-spark/actions/workflows/main.yml/badge.svg?event=push" alt="Unit Tests Badge"/>
  </a>
  <a href="https://github.com/dbt-labs/dbt-spark/actions/workflows/integration.yml">
    <img src="https://github.com/dbt-labs/dbt-spark/actions/workflows/integration.yml/badge.svg?event=push" alt="Integration Tests Badge"/>
  </a>
</p>

**[dbt](https://www.getdbt.com/)** enables data analysts and engineers to transform their data using the same practices that software engineers use to build applications.

dbt is the T in ELT. Organize, cleanse, denormalize, filter, rename, and pre-aggregate the raw data in your warehouse so that it's ready for analysis.

## dbt-spark

The `dbt-spark` package contains all of the code enabling dbt to work with Apache Spark and Databricks. For
more information, consult [the docs](https://docs.getdbt.com/docs/profile-spark).

## Getting started

- [Install dbt](https://docs.getdbt.com/docs/installation)
- Read the [introduction](https://docs.getdbt.com/docs/introduction/) and [viewpoint](https://docs.getdbt.com/docs/about/viewpoint/)

## Running locally
A `docker-compose` environment starts a Spark Thrift server and a Postgres database as a Hive Metastore backend.
Note: dbt-spark now supports Spark 3.1.1 (formerly on Spark 2.x).

The following command would start two docker containers
```
docker-compose up -d
```
It will take a bit of time for the instance to start, you can check the logs of the two containers.
If the instance doesn't start correctly, try the complete reset command listed below and then try start again.

Create a profile like this one:

```
spark-testing:
  target: local
  outputs:
    local:
      type: spark
      method: thrift
      host: 127.0.0.1
      port: 10000
      user: dbt
      schema: analytics
      connect_retries: 5
      connect_timeout: 60
      retry_all: true
```

Connecting to the local spark instance:

* The Spark UI should be available at [http://localhost:4040/sqlserver/](http://localhost:4040/sqlserver/)
* The endpoint for SQL-based testing is at `http://localhost:10000` and can be referenced with the Hive or Spark JDBC drivers using connection string `jdbc:hive2://localhost:10000` and default credentials `dbt`:`dbt`

Note that the Hive metastore data is persisted under `./.hive-metastore/`, and the Spark-produced data under `./.spark-warehouse/`. To completely reset you environment run the following:

```
docker-compose down
rm -rf ./.hive-metastore/
rm -rf ./.spark-warehouse/
```

### Reporting bugs and contributing code

-   Want to report a bug or request a feature? Let us know on [Slack](http://slack.getdbt.com/), or open [an issue](https://github.com/fishtown-analytics/dbt-spark/issues/new).

## Code of Conduct

Everyone interacting in the dbt project's codebases, issue trackers, chat rooms, and mailing lists is expected to follow the [PyPA Code of Conduct](https://www.pypa.io/en/latest/code-of-conduct/).

## Join the dbt Community

- Be part of the conversation in the [dbt Community Slack](http://community.getdbt.com/)
- Read more on the [dbt Community Discourse](https://discourse.getdbt.com)

## Reporting bugs and contributing code

- Want to report a bug or request a feature? Let us know on [Slack](http://community.getdbt.com/), or open [an issue](https://github.com/dbt-labs/dbt-spark/issues/new)
- Want to help us build dbt? Check out the [Contributing Guide](https://github.com/dbt-labs/dbt/blob/HEAD/CONTRIBUTING.md)

## Code of Conduct

Everyone interacting in the dbt project's codebases, issue trackers, chat rooms, and mailing lists is expected to follow the [dbt Code of Conduct](https://community.getdbt.com/code-of-conduct).
















----------------

# JupyterLab Dev Setup

--------------

install Linux package for sasl. If you don't have this package your get this error ```thrift.transport.TTransport.TTransportException: Could not start SASL: b'Error in sasl_client_start (-4) SASL(-4): no mechanism available: No worthy mechs found'```

```bash
sudo apt update
sudo apt install libsasl2-2
sudo apt install python3-pure-sasl
```

Install python packages

```bash
pip install -r dev-requirements.txt
pip install twine
python setup.py install
```

Configure your local spark to use a local warehouse directory. For example we will set it to /tmp/warehouse. Make sure to override these two configurations from spark-defaults.conf.

```

spark.sql.warehouse.dir file:///tmp/warehouse
spark.hadoop.fs.defaultFS file:///


spark.sql.catalog.dbt_spark_test org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.dbt_spark_test.type hadoop
spark.sql.catalog.dbt_spark_test.warehouse file:///tmp/iceberg
spark.sql.catalog.dbt_spark_test.cache-enabled: false

spark.sql.extensions: org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions


```

To see logs of the thrift server

create a verbose log4j file
```
/usr/local/spark/bin/toggle-spark-logging.sh verbose
```

Then add the following to it
```
logger.thrift.name = org.apache.spark.sql.hive.thriftserver
logger.thrift.level = debug
logger.hive.name = org.apache.spark.sql.hive.thriftserver
logger.hive.level = debug
```

Start/Stop local Thrift server

```
/usr/local/spark/sbin/stop-thriftserver.sh 
/usr/local/spark/sbin/start-thriftserver.sh --hiveconf ./docker/hive-site.xml --hiveconf hive.server2.thrift.port=10000 --hiveconf hive.server2.thrift.bind.host=localhost
 ```

Log can be found in this location `/usr/local/spark/logs/`

Run tests using `tox` this will issue these two pytest commands

```
python -m pytest -v --profile apache_spark  -n4 tests/functional/adapter/*
python -m pytest -v -m profile_apache_spark -n4 tests/integration/*

```


Creating a python package for distribution
```
python setup.py sdist
```

