from typing import Optional, TypeVar, Dict, Any, Type
from dataclasses import dataclass, field

from dbt.adapters.base.relation import BaseRelation, Policy
from dbt.utils import deep_merge

from dbt.exceptions import DbtRuntimeError
from dbt.events import AdapterLogger

from dbt.contracts.graph.nodes import SourceDefinition, ResultNode

from dbt.contracts.relation import (
    RelationType,
    ComponentName,
    HasQuoting,
    FakeAPIObject,
    Policy,
    Path,
)

from dbt.utils import filter_null_values, deep_merge, classproperty, merge

import dbt.exceptions

import importlib
import os
from datetime import datetime

logger = AdapterLogger("Spark")

Self = TypeVar("Self", bound="SparkRelation")


@dataclass
class SparkQuotePolicy(Policy):
    database: bool = False
    schema: bool = False
    identifier: bool = False


@dataclass
class SparkIncludePolicy(Policy):
    database: bool = True
    schema: bool = True
    identifier: bool = True


@dataclass(frozen=True, eq=False, repr=False)
class SparkRelation(BaseRelation):
    quote_policy: Policy = field(default_factory=lambda: SparkQuotePolicy())
    include_policy: Policy = field(default_factory=lambda: SparkIncludePolicy())
    quote_character: str = "`"
    is_delta: Optional[bool] = None
    is_hudi: Optional[bool] = None
    is_iceberg: Optional[bool] = None
    # TODO: make this a dict everywhere
    information: Optional[str] = None
    loader: Optional[str] = None
    source_meta: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

    # def __post_init__(self):
    #     if self.database != self.schema and self.database:
    #         raise RuntimeException("Cannot set database in spark!")

    # cccs: create a view from a dataframe
    def load_python_module(self, start_time, end_time, **kwargs):
        logger.debug(f"SparkRelation:load_python_module for source: {self.identifier}")
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        if self.meta and self.meta.get('python_module'):
            path = f"{self.meta.get('python_module')}"
        elif self.source_meta and self.source_meta.get('python_module'):
            path = f"{self.source_meta.get('python_module')}"
        if path:
            logger.debug(f"SparkRelation attempting to load generic python module {path}")
            spec = importlib.util.find_spec(path)
            if not spec:
                raise dbt.exceptions.DbtRuntimeError(f"Cannot find python module {path}")

            python_file = spec.origin
            # file modification timestamp of a file
            mod_time = os.path.getmtime(python_file)
            # convert timestamp into DateTime object
            f_date = datetime.fromtimestamp(mod_time).strftime("%Y%m%d%H%M%S")
            s_date = start_time.strftime("%Y%m%d%H%M%S")
            e_date = end_time.strftime("%Y%m%d%H%M%S")
            view_name = f'{self.identifier}_{f_date}_{s_date}_{e_date}'
            if spark.catalog._jcatalog.tableExists(view_name):
                logger.debug(f"View {view_name} already exists")
            else:
                logger.debug(f"Creating view {view_name}")
                try:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    create_dataframe = getattr(module, "create_dataframe")
                    df = create_dataframe(
                        spark=spark,
                        table_name=self.identifier,
                        start_time=start_time,
                        end_time=end_time,
                        **kwargs)
                    df.createOrReplaceTempView(view_name)
                except Exception as exception :
                    logger.error(f"load_python_module error loading module and creating data frame, {exception.msg}")
                    raise dbt.exceptions.DbtRuntimeError(f"Cannot find python module {path}")
            # Return a relation which only has a table name (spark view have no catalog or schema)
            return SparkRelation.create(database=None, schema=None, identifier=view_name)

    @classmethod
    def create_from_source(cls: Type[Self], source: SourceDefinition, **kwargs: Any) -> Self:
        source_quoting = source.quoting.to_dict(omit_none=True)
        source_quoting.pop("column", None)
        quote_policy = deep_merge(
            cls.get_default_quote_policy().to_dict(omit_none=True),
            source_quoting,
            kwargs.get("quote_policy", {}),
        )

        return cls.create(
            database=source.database,
            schema=source.schema,
            identifier=source.identifier,
            quote_policy=quote_policy,
            loader=source.loader,
            source_meta=source.source_meta,
            meta=source.meta,
            **kwargs,
        )

    @classmethod
    def create_from_node(
            cls: Type[Self],
            config: HasQuoting,
            node,
            quote_policy: Optional[Dict[str, bool]] = None,
            **kwargs: Any,
        ) -> Self:
        if quote_policy is None:
            quote_policy = {}
        quote_policy = merge(config.quoting, quote_policy)

        return cls.create(
            database=config.credentials.database,
            schema=node.schema,
            identifier=node.alias,
            quote_policy=quote_policy,
            meta=node.meta,
            **kwargs,
        )

    def render(self):
        # if self.include_policy.database and self.include_policy.schema:
        #     raise RuntimeException(
        #         "Got a spark relation with schema and database set to "
        #         "include, but only one can be set"
        #     )
        return super().render()

    @classmethod
    def create_from(
            cls: Type[Self],
            config: HasQuoting,
            node: ResultNode,
            **kwargs: Any,
        ) -> Self:
        object_from = super().create_from(config, node, **kwargs)
        return object_from
