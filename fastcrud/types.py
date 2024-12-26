from typing import TypeVar, Any, Union

from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Any)

SelectSchemaType = TypeVar("SelectSchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
UpdateSchemaInternalType = TypeVar("UpdateSchemaInternalType", bound=BaseModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=BaseModel)

GetMultiResponseDict = dict[str, Union[list[dict[str, Any]], int]]
GetMultiResponseModel = dict[str, Union[list[SelectSchemaType], int]]
