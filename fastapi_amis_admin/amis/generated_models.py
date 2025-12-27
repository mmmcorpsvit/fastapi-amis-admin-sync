"""
Basic AMIS Pydantic models - Manual implementation.

Note: The automated generation from schema.json encounters recursion issues
due to the extreme complexity of the AMIS schema (34,000+ lines with deep nesting).

This file provides manually crafted Pydantic models for the most commonly used
AMIS components. For full coverage, consider using TypedDict or plain dicts.

For complete type definitions, refer to the official AMIS schema at:
https://github.com/baidu/amis/releases/latest (schema.json)
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class SchemaType(str, Enum):
    """Common AMIS component types."""

    PAGE = "page"
    FORM = "form"
    BUTTON = "button"
    INPUT_TEXT = "input-text"
    INPUT_EMAIL = "input-email"
    INPUT_PASSWORD = "input-password"
    INPUT_NUMBER = "input-number"
    INPUT_DATE = "input-date"
    INPUT_DATETIME = "input-datetime"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    CHECKBOXES = "checkboxes"
    RADIO = "radio"
    RADIOS = "radios"
    SWITCH = "switch"
    TABLE = "table"
    CRUD = "crud"
    DIALOG = "dialog"
    DRAWER = "drawer"
    ALERT = "alert"
    CARD = "card"
    DIVIDER = "divider"
    HTML = "html"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CAROUSEL = "carousel"
    CHART = "chart"
    CRUD2 = "crud2"
    TABLE2 = "table2"


class BaseSchema(BaseModel):
    """Base schema with common properties."""

    type: str = Field(..., description="Component type")
    class_name: Optional[str] = Field(None, alias="className", description="CSS class name")
    disabled: Optional[bool] = Field(None, description="Whether disabled")
    hidden: Optional[bool] = Field(None, description="Whether hidden")
    visible: Optional[bool] = Field(None, description="Whether visible")
    id: Optional[str] = Field(None, description="Unique component ID")
    style: Optional[Dict[str, Any]] = Field(None, description="Custom styles")

    class Config:
        populate_by_name = True
        use_enum_values = True


class Option(BaseModel):
    """Select/Radio option."""

    label: str = Field(..., description="Display label")
    value: Union[str, int, bool] = Field(..., description="Option value")
    disabled: Optional[bool] = Field(None, description="Whether disabled")


class FormControl(BaseSchema):
    """Base form control."""

    name: str = Field(..., description="Field name")
    label: Optional[str] = Field(None, description="Field label")
    required: Optional[bool] = Field(None, description="Whether required")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    description: Optional[str] = Field(None, description="Help text")
    value: Optional[Any] = Field(None, description="Default value")


class InputText(FormControl):
    """Text input component."""

    type: str = Field("input-text", alias="type")
    max_length: Optional[int] = Field(None, alias="maxLength")
    min_length: Optional[int] = Field(None, alias="minLength")
    clearable: Optional[bool] = Field(None, description="Show clear button")


class InputEmail(FormControl):
    """Email input component."""

    type: str = Field("input-email", alias="type")


class InputPassword(FormControl):
    """Password input component."""

    type: str = Field("input-password", alias="type")


class InputNumber(FormControl):
    """Number input component."""

    type: str = Field("input-number", alias="type")
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")
    step: Optional[float] = Field(None, description="Step value")


class Select(FormControl):
    """Select component."""

    type: str = Field("select", alias="type")
    options: List[Option] = Field(default_factory=list, description="Select options")
    multiple: Optional[bool] = Field(None, description="Allow multiple selection")
    checkable: Optional[bool] = Field(None, description="Show checkbox")


class Switch(FormControl):
    """Switch component."""

    type: str = Field("switch", alias="type")
    option: Optional[str] = Field(None, description="Option text")


class Button(BaseSchema):
    """Button component."""

    type: str = Field("button", alias="type")
    label: str = Field(..., description="Button text")
    level: Optional[str] = Field(None, description="Button level: primary, secondary, etc")
    size: Optional[str] = Field(None, description="Button size: xs, sm, md, lg")
    action_type: Optional[str] = Field(None, alias="actionType", description="Action type")


class Column(BaseModel):
    """Table column definition."""

    name: str = Field(..., description="Column field name")
    label: Optional[str] = Field(None, description="Column header label")
    type: Optional[str] = Field(None, description="Column type")
    sortable: Optional[bool] = Field(None, description="Whether sortable")
    searchable: Optional[bool] = Field(None, description="Whether searchable")
    width: Optional[Union[int, str]] = Field(None, description="Column width")


class Form(BaseSchema):
    """Form component."""

    type: str = Field("form", alias="type")
    title: Optional[str] = Field(None, description="Form title")
    body: List[Union[Dict[str, Any], FormControl]] = Field(
        default_factory=list, description="Form controls"
    )
    api: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Submit API")
    init_api: Optional[Union[str, Dict[str, Any]]] = Field(
        None, alias="initApi", description="Initialize API"
    )
    mode: Optional[str] = Field(None, description="Form layout mode: normal, horizontal, inline")


class CRUD(BaseSchema):
    """CRUD component."""

    type: str = Field("crud", alias="type")
    api: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Data API")
    columns: List[Column] = Field(default_factory=list, description="Table columns")
    filter: Optional[Union[Dict[str, Any], Form]] = Field(None, description="Filter form")
    bulk_actions: List[Dict[str, Any]] = Field(
        default_factory=list, alias="bulkActions", description="Bulk actions"
    )
    per_page: Optional[int] = Field(None, alias="perPage", description="Items per page")


class Page(BaseSchema):
    """Page component - top level container."""

    type: str = Field("page", alias="type")
    title: Optional[str] = Field(None, description="Page title")
    sub_title: Optional[str] = Field(None, alias="subTitle", description="Page subtitle")
    body: List[Union[Dict[str, Any], BaseSchema]] = Field(
        default_factory=list, description="Page body content"
    )
    aside: Optional[List[Dict[str, Any]]] = Field(None, description="Sidebar content")
    toolbar: Optional[List[Dict[str, Any]]] = Field(None, description="Toolbar content")
    init_api: Optional[Union[str, Dict[str, Any]]] = Field(
        None, alias="initApi", description="Initialize API"
    )
    css: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Custom CSS")


# Alias for convenience
Schema = Page


# Export all models
__all__ = [
    "SchemaType",
    "BaseSchema",
    "Option",
    "FormControl",
    "InputText",
    "InputEmail",
    "InputPassword",
    "InputNumber",
    "Select",
    "Switch",
    "Button",
    "Column",
    "Form",
    "CRUD",
    "Page",
    "Schema",
]
