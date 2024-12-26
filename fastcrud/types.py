from typing import TypeVar, Any, Dict, Union, List

from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Any)

SelectSchemaType = TypeVar("SelectSchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
UpdateSchemaInternalType = TypeVar("UpdateSchemaInternalType", bound=BaseModel)
DeleteSchemaType = TypeVar("DeleteSchemaType", bound=BaseModel)

GetMultiResponseDict = Dict[str, Union[List[Dict[str, Any]], int]]
GetMultiResponseModel = Dict[str, Union[List[SelectSchemaType], int]]
