#!/usr/bin/env python3
"""
Translate Chinese descriptions in AMIS schema to English using dictionary mapping.

This script provides translations for common AMIS Chinese terms without
requiring external translation libraries.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "schema.json"
OUTPUT_PATH = Path(__file__).parent.parent / "schema" / "schema_translated.json"

# Common AMIS Chinese to English translations
TRANSLATIONS = {
    # Component types
    "指定为 page 渲染器。": "Specifies the page renderer.",
    "指定为 form 渲染器。": "Specifies the form renderer.",
    "指定为 crud 渲染器。": "Specifies the CRUD renderer.",
    "指定为 table 渲染器。": "Specifies the table renderer.",
    
    # Page properties
    "页面标题": "Page title",
    "页面副标题": "Page subtitle",
    "页面描述, 标题旁边会出现个小图标，放上去会显示这个属性配置的内容。": "Page description. A small icon appears next to the title, hovering over it reveals the content configured in this property.",
    "内容区域": "Content area",
    "内容区 css 类名": "Content area CSS class name",
    "边栏区域": "Sidebar area",
    "边栏是否允许拖动": "Whether the sidebar allows dragging",
    "边栏内容是否粘住，即不跟随滚动。": "Whether the sidebar content is sticky, i.e. does not scroll with the page.",
    "边栏位置": "Sidebar position",
    "边栏最小宽度": "Minimum sidebar width",
    "边栏最大宽度": "Maximum sidebar width",
    "边栏区 css 类名": "Sidebar area CSS class name",
    "自定义页面级别样式表": "Custom page-level stylesheet",
    "移动端下的样式表": "Stylesheet for mobile devices",
    "页面级别的初始数据": "Page-level initial data",
    
    # Common properties
    "配置容器 className": "Configure container className",
    "配置 header 容器 className": "Configure header container className",
    "组件唯一 id，主要用于页面设计器中定位 json 节点": "Unique component ID, mainly used to locate JSON nodes in the page designer",
    "组件唯一 id，主要用于日志采集": "Unique component ID, mainly used for log collection",
    "组件名字，这个名字可以用来定位，用于组件通信": "Component name, this name can be used for positioning and component communication",
    "是否禁用": "Whether disabled",
    "是否隐藏": "Whether hidden",
    "是否显示": "Whether visible",
    "是否静态展示": "Whether to display statically",
    "静态展示空值占位": "Static display empty value placeholder",
    "组件样式": "Component style",
    "编辑器配置，运行时可以忽略": "Editor configuration, can be ignored at runtime",
    "可以组件级别用来关闭移动端样式": "Can be used at the component level to turn off mobile styles",
    
    # API related
    "页面初始化的时候，可以设置一个 API 让其取拉取，发送数据会携带当前 data 数据（包含地址栏参数），获取得数据会合并到 data 中，供组件内使用。": "When the page is initialized, you can set an API to fetch data. The sent data will carry the current data (including URL parameters), and the fetched data will be merged into data for use within components.",
    "是否默认就拉取？": "Whether to fetch by default?",
    
    # Expression related
    "表达式，语法 `${xxx > 5}`。": "Expression, syntax `${xxx > 5}`.",
    
    # CSS related
    "css类名，配置字符串，或者对象。\n\n    className: \"red\"\n\n用对象配置时意味着你能跟表达式一起搭配使用，如：\n\n    className: {         \"red\": \"data.progress > 80\",         \"blue\": \"data.progress > 60\"     }": "CSS class name, configured as a string or object.\n\n    className: \"red\"\n\nWhen configured as an object, it means you can use it with expressions, such as:\n\n    className: {         \"red\": \"data.progress > 80\",         \"blue\": \"data.progress > 60\"     }",
    
    # Template related
    "支持两种语法，但是不能混着用。分别是：\n\n1. `${xxx}` 或者 `${xxx|upperCase}` 2. `<%= data.xxx %>`\n\n\n更多文档：https://aisuda.bce.baidu.com/amis/zh-CN/docs/concepts/template": "Supports two syntaxes, but they cannot be mixed. They are:\n\n1. `${xxx}` or `${xxx|upperCase}` 2. `<%= data.xxx %>`\n\n\nMore documentation: https://aisuda.bce.baidu.com/amis/zh-CN/docs/concepts/template",
    
    # Icon related
    "iconfont 里面的类名。": "Class name in iconfont.",
    "触发规则": "Trigger rules",
    "提示标题": "Tooltip title",
    "显示位置": "Display position",
    "点击其他内容时是否关闭弹框信息": "Whether to close the popup when clicking elsewhere",
    "icon的形状": "Icon shape",
    
    # Data related
    "初始数据，设置得值可用于组件内部模板使用。": "Initial data, the set value can be used in component internal templates.",
    
    # Messages related
    "消息文案配置，记住这个优先级是最低的，如果你的接口返回了 msg，接口返回的优先。": "Message text configuration. Remember that this has the lowest priority. If your interface returns a msg, the interface return takes precedence.",
    
    # Polling related
    "配置轮询间隔，配置后 initApi 将轮询加载。": "Configure polling interval. After configuration, initApi will load by polling.",
    "是否要静默加载，也就是说不显示进度": "Whether to load silently, i.e. without showing progress",
    "是否显示错误信息，默认是显示的。": "Whether to display error messages. By default, they are displayed.",
    
    # Regions
    "默认不设置自动感觉内容来决定要不要展示这些区域 如果配置了，以配置为主。": "By default, it automatically senses the content to decide whether to display these areas. If configured, the configuration takes precedence.",
    
    # Pull refresh
    "下拉刷新配置": "Pull-to-refresh configuration",
    
    # CSS variables
    "css 变量": "CSS variables",
    
    # Event actions
    "事件动作配置": "Event action configuration",
    
    # Schema references
    "配合 definitions 一起使用，可以实现无限循环的渲染器。": "Used together with definitions, infinite loop renderers can be achieved.",
}


def contains_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    if not isinstance(text, str):
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def translate_text(text: str) -> str:
    """
    Translate Chinese text to English using dictionary lookup.
    
    Args:
        text: Text to translate
    
    Returns:
        Translated text (or original if no translation found)
    """
    if not contains_chinese(text):
        return text
    
    # Try exact match first
    if text in TRANSLATIONS:
        return TRANSLATIONS[text]
    
    # Try to replace Chinese characters with English where possible
    result = text
    for chinese, english in TRANSLATIONS.items():
        if chinese in result:
            result = result.replace(chinese, english)
    
    # If still contains Chinese, log it
    if contains_chinese(result) and result == text:
        logger.debug(f"No translation for: {text[:80]}...")
    
    return result


def translate_schema_recursive(obj: Any, path: str = "") -> Any:
    """
    Recursively translate Chinese text in schema.
    
    Args:
        obj: Schema object (dict, list, or primitive)
        path: Current path in schema (for logging)
    
    Returns:
        Translated schema object
    """
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            
            # Translate description and title fields
            if key in ("description", "title") and isinstance(value, str):
                result[key] = translate_text(value)
            # Recursively process nested structures
            else:
                result[key] = translate_schema_recursive(value, current_path)
        
        return result
    
    elif isinstance(obj, list):
        return [
            translate_schema_recursive(item, f"{path}[{i}]")
            for i, item in enumerate(obj)
        ]
    
    elif isinstance(obj, str):
        # Translate standalone strings
        return translate_text(obj)
    
    else:
        return obj


def main():
    """Main function to translate schema."""
    logger.info("=" * 60)
    logger.info("AMIS Schema Translation (Chinese -> English)")
    logger.info("=" * 60)
    
    # Load schema
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Count Chinese strings
    schema_str = json.dumps(schema, ensure_ascii=False)
    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', schema_str))
    logger.info(f"Found ~{chinese_count} Chinese characters")
    
    # Translate schema
    logger.info(f"Translating schema using {len(TRANSLATIONS)} dictionary entries...")
    translated_schema = translate_schema_recursive(schema)
    
    # Save translated schema
    logger.info(f"Saving translated schema to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(translated_schema, f, indent=2, ensure_ascii=False)
    
    # Verify translation
    translated_str = json.dumps(translated_schema, ensure_ascii=False)
    remaining_chinese = len(re.findall(r'[\u4e00-\u9fff]', translated_str))
    
    logger.info("=" * 60)
    logger.info(f"✅ Translation complete!")
    logger.info(f"Original Chinese characters: {chinese_count}")
    logger.info(f"Remaining Chinese characters: {remaining_chinese}")
    if chinese_count > 0:
        logger.info(f"Translation rate: {((chinese_count - remaining_chinese) / chinese_count * 100):.1f}%")
    logger.info(f"Output: {OUTPUT_PATH}")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
